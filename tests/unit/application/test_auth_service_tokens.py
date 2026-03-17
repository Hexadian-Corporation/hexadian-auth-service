from datetime import datetime, timedelta
from unittest.mock import MagicMock

import jwt
import pytest

from src.application.ports.inbound.rbac_service import RbacService
from src.application.ports.outbound.auth_code_repository import AuthCodeRepository
from src.application.ports.outbound.group_repository import GroupRepository
from src.application.ports.outbound.refresh_token_repository import RefreshTokenRepository
from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher
from src.application.ports.outbound.user_repository import UserRepository
from src.application.services.auth_service_impl import AuthServiceImpl
from src.domain.exceptions.user_exceptions import (
    InvalidCredentialsError,
    RefreshTokenNotFoundError,
    UserNotFoundError,
)
from src.domain.models.rbac_claims import RbacClaims
from src.domain.models.refresh_token import RefreshToken
from src.domain.models.user import User
from src.infrastructure.config.settings import Settings


@pytest.fixture()
def mock_repository() -> MagicMock:
    return MagicMock(spec=UserRepository)


@pytest.fixture()
def mock_rsi_fetcher() -> MagicMock:
    return MagicMock(spec=RsiProfileFetcher)


@pytest.fixture()
def mock_refresh_token_repository() -> MagicMock:
    return MagicMock(spec=RefreshTokenRepository)


@pytest.fixture()
def mock_auth_code_repository() -> MagicMock:
    return MagicMock(spec=AuthCodeRepository)


@pytest.fixture()
def mock_group_repository() -> MagicMock:
    return MagicMock(spec=GroupRepository)


@pytest.fixture()
def mock_rbac_service() -> MagicMock:
    mock = MagicMock(spec=RbacService)
    mock.resolve_rbac_claims.return_value = RbacClaims()
    return mock


@pytest.fixture()
def settings() -> Settings:
    return Settings(jwt_secret="test-secret", jwt_expiration_minutes=15, jwt_refresh_expiration_days=7)


@pytest.fixture()
def service(
    mock_repository: MagicMock,
    mock_rsi_fetcher: MagicMock,
    mock_refresh_token_repository: MagicMock,
    mock_auth_code_repository: MagicMock,
    mock_group_repository: MagicMock,
    mock_rbac_service: MagicMock,
    settings: Settings,
) -> AuthServiceImpl:
    return AuthServiceImpl(
        repository=mock_repository,
        rsi_profile_fetcher=mock_rsi_fetcher,
        refresh_token_repository=mock_refresh_token_repository,
        auth_code_repository=mock_auth_code_repository,
        group_repository=mock_group_repository,
        rbac_service=mock_rbac_service,
        settings=settings,
    )


def _make_user(**overrides: object) -> User:
    defaults = {
        "id": "user-1",
        "username": "testuser",
        "hashed_password": "",
        "rsi_handle": "TestPilot",
        "rsi_verified": False,
    }
    defaults.update(overrides)
    return User(**defaults)


class TestAuthenticate:
    def test_authenticate_returns_token_response(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
        settings: Settings,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("secret"))
        mock_repository.find_by_username.return_value = user
        mock_refresh_token_repository.save.side_effect = lambda t: t

        result = service.authenticate("testuser", "secret")

        assert result.token_type == "bearer"
        assert result.expires_in == 900
        assert isinstance(result.access_token, str)
        assert isinstance(result.refresh_token, str)

    def test_authenticate_access_token_has_correct_claims(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
        settings: Settings,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("secret"))
        mock_repository.find_by_username.return_value = user
        mock_refresh_token_repository.save.side_effect = lambda t: t

        result = service.authenticate("testuser", "secret")

        decoded = jwt.decode(result.access_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert decoded["sub"] == "user-1"
        assert decoded["username"] == "testuser"
        assert decoded["rsi_handle"] == "TestPilot"
        assert decoded["rsi_verified"] is False
        assert decoded["groups"] == []
        assert decoded["roles"] == []
        assert decoded["permissions"] == []
        assert "iat" in decoded
        assert "exp" in decoded

    def test_authenticate_access_token_expires_in_15_minutes(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
        settings: Settings,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("secret"))
        mock_repository.find_by_username.return_value = user
        mock_refresh_token_repository.save.side_effect = lambda t: t

        result = service.authenticate("testuser", "secret")

        decoded = jwt.decode(result.access_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        exp = decoded["exp"]
        iat = decoded["iat"]
        assert exp - iat == 15 * 60

    def test_authenticate_saves_refresh_token(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("secret"))
        mock_repository.find_by_username.return_value = user
        mock_refresh_token_repository.save.side_effect = lambda t: t

        service.authenticate("testuser", "secret")

        mock_refresh_token_repository.save.assert_called_once()
        saved_token = mock_refresh_token_repository.save.call_args[0][0]
        assert saved_token.user_id == "user-1"
        assert len(saved_token.token) == 36  # UUID format

    def test_authenticate_invalid_credentials_raises(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.find_by_username.return_value = None

        with pytest.raises(InvalidCredentialsError):
            service.authenticate("testuser", "wrong")

    def test_authenticate_wrong_password_raises(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("correct"))
        mock_repository.find_by_username.return_value = user

        with pytest.raises(InvalidCredentialsError):
            service.authenticate("testuser", "wrong")


class TestRefreshToken:
    def test_refresh_token_returns_new_token_pair(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
        settings: Settings,
    ) -> None:
        user = _make_user()
        existing = RefreshToken(
            id="rt-1",
            user_id="user-1",
            token="old-refresh-token",
            expires_at=datetime.now(tz=datetime.now().astimezone().tzinfo) + timedelta(days=1),
        )
        mock_refresh_token_repository.find_by_token.return_value = existing
        mock_repository.find_by_id.return_value = user
        mock_refresh_token_repository.save.side_effect = lambda t: t

        result = service.refresh_token("old-refresh-token")

        assert result.token_type == "bearer"
        assert result.access_token is not None
        assert result.refresh_token != "old-refresh-token"

    def test_refresh_token_revokes_old_token(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        user = _make_user()
        existing = RefreshToken(
            id="rt-1",
            user_id="user-1",
            token="old-refresh-token",
            expires_at=datetime.now(tz=datetime.now().astimezone().tzinfo) + timedelta(days=1),
        )
        mock_refresh_token_repository.find_by_token.return_value = existing
        mock_repository.find_by_id.return_value = user
        mock_refresh_token_repository.save.side_effect = lambda t: t

        service.refresh_token("old-refresh-token")

        mock_refresh_token_repository.revoke.assert_called_once_with("old-refresh-token")

    def test_refresh_token_not_found_raises(
        self,
        service: AuthServiceImpl,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        mock_refresh_token_repository.find_by_token.return_value = None

        with pytest.raises(RefreshTokenNotFoundError):
            service.refresh_token("nonexistent")

    def test_refresh_token_revoked_raises(
        self,
        service: AuthServiceImpl,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        existing = RefreshToken(
            id="rt-1",
            user_id="user-1",
            token="revoked-token",
            expires_at=datetime.now(tz=datetime.now().astimezone().tzinfo) + timedelta(days=1),
            revoked=True,
        )
        mock_refresh_token_repository.find_by_token.return_value = existing

        with pytest.raises(RefreshTokenNotFoundError):
            service.refresh_token("revoked-token")

    def test_refresh_token_expired_raises(
        self,
        service: AuthServiceImpl,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        existing = RefreshToken(
            id="rt-1",
            user_id="user-1",
            token="expired-token",
            expires_at=datetime.now(tz=datetime.now().astimezone().tzinfo) - timedelta(days=1),
        )
        mock_refresh_token_repository.find_by_token.return_value = existing

        with pytest.raises(RefreshTokenNotFoundError):
            service.refresh_token("expired-token")

    def test_refresh_token_user_not_found_raises(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        existing = RefreshToken(
            id="rt-1",
            user_id="deleted-user",
            token="valid-token",
            expires_at=datetime.now(tz=datetime.now().astimezone().tzinfo) + timedelta(days=1),
        )
        mock_refresh_token_repository.find_by_token.return_value = existing
        mock_repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            service.refresh_token("valid-token")

    def test_refresh_token_re_resolves_user_claims(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
        settings: Settings,
    ) -> None:
        user = _make_user(rsi_verified=True)
        existing = RefreshToken(
            id="rt-1",
            user_id="user-1",
            token="old-token",
            expires_at=datetime.now(tz=datetime.now().astimezone().tzinfo) + timedelta(days=1),
        )
        mock_refresh_token_repository.find_by_token.return_value = existing
        mock_repository.find_by_id.return_value = user
        mock_refresh_token_repository.save.side_effect = lambda t: t

        result = service.refresh_token("old-token")

        decoded = jwt.decode(result.access_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert decoded["rsi_verified"] is True


class TestRevokeToken:
    def test_revoke_token_success(
        self,
        service: AuthServiceImpl,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        existing = RefreshToken(
            id="rt-1",
            user_id="user-1",
            token="token-to-revoke",
        )
        mock_refresh_token_repository.find_by_token.return_value = existing

        service.revoke_token("token-to-revoke")

        mock_refresh_token_repository.revoke.assert_called_once_with("token-to-revoke")

    def test_revoke_token_not_found_raises(
        self,
        service: AuthServiceImpl,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        mock_refresh_token_repository.find_by_token.return_value = None

        with pytest.raises(RefreshTokenNotFoundError):
            service.revoke_token("nonexistent")


class TestRbacClaims:
    def test_login_jwt_contains_rbac_claims(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
        mock_rbac_service: MagicMock,
        settings: Settings,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("secret"))
        mock_repository.find_by_username.return_value = user
        mock_refresh_token_repository.save.side_effect = lambda t: t
        mock_rbac_service.resolve_rbac_claims.return_value = RbacClaims(
            groups=["Admins"],
            roles=["Super Admin"],
            permissions=["hhh:contracts:read", "hhh:contracts:write"],
        )

        result = service.authenticate("testuser", "secret")

        decoded = jwt.decode(result.access_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert decoded["groups"] == ["Admins"]
        assert decoded["roles"] == ["Super Admin"]
        assert decoded["permissions"] == ["hhh:contracts:read", "hhh:contracts:write"]

    def test_refresh_re_resolves_rbac_claims_from_db(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
        mock_rbac_service: MagicMock,
        settings: Settings,
    ) -> None:
        user = _make_user()
        existing = RefreshToken(
            id="rt-1",
            user_id="user-1",
            token="old-token",
            expires_at=datetime.now(tz=datetime.now().astimezone().tzinfo) + timedelta(days=1),
        )
        mock_refresh_token_repository.find_by_token.return_value = existing
        mock_repository.find_by_id.return_value = user
        mock_refresh_token_repository.save.side_effect = lambda t: t
        mock_rbac_service.resolve_rbac_claims.return_value = RbacClaims(
            groups=["Users"],
            roles=["Member"],
            permissions=["hhh:contracts:read"],
        )

        result = service.refresh_token("old-token")

        decoded = jwt.decode(result.access_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert decoded["groups"] == ["Users"]
        assert decoded["roles"] == ["Member"]
        assert decoded["permissions"] == ["hhh:contracts:read"]
        mock_rbac_service.resolve_rbac_claims.assert_called_once_with(user.id)

    def test_token_with_no_groups_has_empty_claims(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
        mock_rbac_service: MagicMock,
        settings: Settings,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("secret"))
        mock_repository.find_by_username.return_value = user
        mock_refresh_token_repository.save.side_effect = lambda t: t
        mock_rbac_service.resolve_rbac_claims.return_value = RbacClaims()

        result = service.authenticate("testuser", "secret")

        decoded = jwt.decode(result.access_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert decoded["groups"] == []
        assert decoded["roles"] == []
        assert decoded["permissions"] == []

    def test_token_with_multiple_groups_deduplicates_permissions(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
        mock_rbac_service: MagicMock,
        settings: Settings,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("secret"))
        mock_repository.find_by_username.return_value = user
        mock_refresh_token_repository.save.side_effect = lambda t: t
        mock_rbac_service.resolve_rbac_claims.return_value = RbacClaims(
            groups=["Admins", "Users"],
            roles=["Super Admin", "Member"],
            permissions=["hhh:contracts:read", "hhh:contracts:write", "auth:users:admin"],
        )

        result = service.authenticate("testuser", "secret")

        decoded = jwt.decode(result.access_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert decoded["groups"] == ["Admins", "Users"]
        assert decoded["roles"] == ["Super Admin", "Member"]
        assert decoded["permissions"] == ["hhh:contracts:read", "hhh:contracts:write", "auth:users:admin"]

    def test_refresh_picks_up_permission_changes(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
        mock_rbac_service: MagicMock,
        settings: Settings,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("secret"))
        mock_repository.find_by_username.return_value = user
        mock_refresh_token_repository.save.side_effect = lambda t: t

        mock_rbac_service.resolve_rbac_claims.return_value = RbacClaims(
            groups=["Users"],
            roles=["Member"],
            permissions=["hhh:contracts:read"],
        )
        login_result = service.authenticate("testuser", "secret")
        login_decoded = jwt.decode(login_result.access_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert login_decoded["permissions"] == ["hhh:contracts:read"]

        existing = RefreshToken(
            id="rt-1",
            user_id="user-1",
            token=login_result.refresh_token,
            expires_at=datetime.now(tz=datetime.now().astimezone().tzinfo) + timedelta(days=1),
        )
        mock_refresh_token_repository.find_by_token.return_value = existing
        mock_repository.find_by_id.return_value = user

        mock_rbac_service.resolve_rbac_claims.return_value = RbacClaims(
            groups=["Admins", "Users"],
            roles=["Super Admin", "Member"],
            permissions=["hhh:contracts:read", "hhh:contracts:write", "auth:users:admin"],
        )
        refresh_result = service.refresh_token(login_result.refresh_token)
        refresh_decoded = jwt.decode(
            refresh_result.access_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        assert refresh_decoded["groups"] == ["Admins", "Users"]
        assert refresh_decoded["roles"] == ["Super Admin", "Member"]
        assert refresh_decoded["permissions"] == ["hhh:contracts:read", "hhh:contracts:write", "auth:users:admin"]
