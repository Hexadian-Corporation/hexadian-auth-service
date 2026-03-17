from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from hexadian_auth_common.context import UserContext
from hexadian_auth_common.fastapi import _stub_jwt_auth, require_permission

from src.application.ports.inbound.auth_service import AuthService
from src.domain.exceptions.app_signature_exceptions import InvalidAppSignatureError
from src.domain.exceptions.user_exceptions import (
    InvalidAuthCodeError,
    InvalidCredentialsError,
    InvalidPasswordError,
    InvalidRedirectUriError,
    RefreshTokenNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.infrastructure.adapters.inbound.api.auth_api_mapper import AuthApiMapper
from src.infrastructure.adapters.inbound.api.auth_dto import (
    AuthorizeDTO,
    AuthorizeResponseDTO,
    LoginDTO,
    PasswordChangeDTO,
    PasswordResetDTO,
    RefreshTokenDTO,
    RegisterDTO,
    StartVerificationDTO,
    TokenDTO,
    TokenExchangeDTO,
    TokenIntrospectRequestDTO,
    TokenIntrospectResponseDTO,
    UserDTO,
    UserUpdateDTO,
    VerificationResultDTO,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_auth_service: AuthService | None = None


def init_router(auth_service: AuthService) -> None:
    global _auth_service
    _auth_service = auth_service


@router.post("/register", response_model=UserDTO, status_code=201)
def register(dto: RegisterDTO) -> UserDTO:
    try:
        user = _auth_service.register(dto.username, dto.password, dto.rsi_handle, dto.app_id, dto.app_signature)
    except InvalidAppSignatureError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except UserAlreadyExistsError as exc:
        detail = "Username already taken" if exc.field == "username" else "RSI handle already registered"
        raise HTTPException(status_code=409, detail={"message": detail, "field": exc.field}) from exc
    return AuthApiMapper.to_dto(user)


@router.post("/login", response_model=TokenDTO)
def login(dto: LoginDTO) -> TokenDTO:
    try:
        token_response = _auth_service.authenticate(dto.username, dto.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return TokenDTO(
        access_token=token_response.access_token,
        refresh_token=token_response.refresh_token,
        token_type=token_response.token_type,
        expires_in=token_response.expires_in,
    )


@router.post("/token/refresh", response_model=TokenDTO)
def refresh_token(dto: RefreshTokenDTO) -> TokenDTO:
    try:
        token_response = _auth_service.refresh_token(dto.refresh_token)
    except RefreshTokenNotFoundError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except UserNotFoundError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return TokenDTO(
        access_token=token_response.access_token,
        refresh_token=token_response.refresh_token,
        token_type=token_response.token_type,
        expires_in=token_response.expires_in,
    )


@router.post("/token/revoke", status_code=204)
def revoke_token(dto: RefreshTokenDTO) -> None:
    try:
        _auth_service.revoke_token(dto.refresh_token)
    except RefreshTokenNotFoundError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/users/{user_id}", response_model=UserDTO)
def get_user(user_id: str, user_ctx: Annotated[UserContext, Depends(_stub_jwt_auth)]) -> UserDTO:
    if user_ctx.user_id != user_id and "users:read" not in user_ctx.permissions:
        raise HTTPException(status_code=403, detail="Missing required permission: users:read")
    try:
        target_user = _auth_service.get_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AuthApiMapper.to_dto(target_user)


@router.get("/users", response_model=list[UserDTO], dependencies=[Depends(require_permission("users:read"))])
def list_users() -> list[UserDTO]:
    return [AuthApiMapper.to_dto(u) for u in _auth_service.list_users()]


@router.delete("/users/{user_id}", status_code=204, dependencies=[Depends(require_permission("users:admin"))])
def delete_user(user_id: str) -> None:
    try:
        _auth_service.delete_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/users/{user_id}", response_model=UserDTO)
def update_user(
    user_id: str,
    dto: UserUpdateDTO,
    user_ctx: Annotated[UserContext, Depends(_stub_jwt_auth)],
) -> UserDTO:
    if user_ctx.user_id != user_id and "users:admin" not in user_ctx.permissions:
        raise HTTPException(status_code=403, detail="Missing required permission: users:admin")
    updates = dto.model_dump(exclude_none=True)
    try:
        user = _auth_service.update_user(user_id, updates)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UserAlreadyExistsError as exc:
        detail = "Username already taken" if exc.field == "username" else "RSI handle already registered"
        raise HTTPException(status_code=409, detail={"message": detail, "field": exc.field}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthApiMapper.to_dto(user)


@router.post("/verify/start", response_model=VerificationResultDTO, dependencies=[Depends(_stub_jwt_auth)])
def start_verification(dto: StartVerificationDTO, user_id: str) -> VerificationResultDTO:
    try:
        code = _auth_service.start_verification(user_id, dto.rsi_handle)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return VerificationResultDTO(
        verification_code=code,
        verified=False,
        message=(
            "Add the verification code to your RSI profile bio at "
            "https://robertsspaceindustries.com/account/profile and then call /auth/verify/confirm"
        ),
    )


@router.post("/verify/confirm", response_model=VerificationResultDTO, dependencies=[Depends(_stub_jwt_auth)])
def confirm_verification(user_id: str) -> VerificationResultDTO:
    try:
        verified = _auth_service.confirm_verification(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if verified:
        return VerificationResultDTO(verified=True, message="RSI account verified successfully")
    return VerificationResultDTO(verified=False, message="Verification code not found in RSI profile bio")


@router.post("/authorize", response_model=AuthorizeResponseDTO)
def authorize(dto: AuthorizeDTO) -> AuthorizeResponseDTO:
    try:
        auth_code = _auth_service.authorize(dto.username, dto.password, dto.redirect_uri, dto.state)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except InvalidRedirectUriError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthorizeResponseDTO(
        code=auth_code.code,
        state=auth_code.state,
        redirect_uri=auth_code.redirect_uri,
    )


@router.post("/token/exchange", response_model=TokenDTO)
def exchange_token(dto: TokenExchangeDTO) -> TokenDTO:
    try:
        token_response = _auth_service.exchange_code(dto.code, dto.redirect_uri)
    except InvalidAuthCodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except UserNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TokenDTO(
        access_token=token_response.access_token,
        refresh_token=token_response.refresh_token,
        token_type=token_response.token_type,
        expires_in=token_response.expires_in,
    )


@router.post("/password/change", status_code=204)
def change_password(
    dto: PasswordChangeDTO,
    user_ctx: Annotated[UserContext, Depends(_stub_jwt_auth)],
) -> None:
    try:
        _auth_service.change_password(user_ctx.user_id, dto.old_password, dto.new_password)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidPasswordError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/users/{user_id}/password-reset",
    status_code=204,
    dependencies=[Depends(require_permission("users:admin"))],
)
def reset_password(user_id: str, dto: PasswordResetDTO) -> None:
    try:
        _auth_service.reset_password(user_id, dto.new_password)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidPasswordError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/token/introspect", response_model=TokenIntrospectResponseDTO)
def introspect_token(dto: TokenIntrospectRequestDTO) -> TokenIntrospectResponseDTO:
    result = _auth_service.introspect_token(dto.token)
    return TokenIntrospectResponseDTO(
        active=result.active,
        sub=result.sub,
        username=result.username,
        groups=result.groups,
        roles=result.roles,
        permissions=result.permissions,
        rsi_handle=result.rsi_handle,
        rsi_verified=result.rsi_verified,
        exp=result.exp,
        iat=result.iat,
        is_user_active=result.is_user_active,
        reason=result.reason,
    )
