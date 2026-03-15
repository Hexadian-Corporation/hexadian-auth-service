from fastapi import APIRouter, HTTPException

from src.application.ports.inbound.auth_service import AuthService
from src.domain.exceptions.user_exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.infrastructure.adapters.inbound.api.auth_api_mapper import AuthApiMapper
from src.infrastructure.adapters.inbound.api.auth_dto import (
    LoginDTO,
    RegisterDTO,
    StartVerificationDTO,
    TokenDTO,
    UserDTO,
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
        user = _auth_service.register(dto.username, dto.email, dto.password)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AuthApiMapper.to_dto(user)


@router.post("/login", response_model=TokenDTO)
def login(dto: LoginDTO) -> TokenDTO:
    try:
        token = _auth_service.authenticate(dto.username, dto.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return TokenDTO(access_token=token)


@router.get("/users/{user_id}", response_model=UserDTO)
def get_user(user_id: str) -> UserDTO:
    try:
        user = _auth_service.get_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AuthApiMapper.to_dto(user)


@router.get("/users", response_model=list[UserDTO])
def list_users() -> list[UserDTO]:
    return [AuthApiMapper.to_dto(u) for u in _auth_service.list_users()]


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str) -> None:
    try:
        _auth_service.delete_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/verify/start", response_model=VerificationResultDTO)
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


@router.post("/verify/confirm", response_model=VerificationResultDTO)
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
