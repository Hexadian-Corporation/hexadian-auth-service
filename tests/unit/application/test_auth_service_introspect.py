from datetime import UTC, datetime, timedelta
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
from src.domain.models.rbac_claims import RbacClaims
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


def _make_access_token(settings: Settings, **overrides: object) -> str:
    now = datetime.now(tz=UTC)
    payload: dict = {
        "sub": "user-1",
        "username": "testuser",
        "groups": ["Admins"],
        "roles": ["Super Admin"],
        "permissions": ["hhh:contracts:read", "hhh:contracts:write"],
        "rsi_handle": "TestPilot",
        "rsi_verified": False,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expiration_minutes),
    }
    payload.update(overrides)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


class TestIntrospectTokenActiveUser:
    def test_valid_token_active_user_returns_active_true(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        settings: Settings,
    ) -> None:
        token = _make_access_token(settings)
        mock_repository.find_by_id.return_value = _make_user()

        result = service.introspect_token(token)

        assert result.active is True
        assert result.sub == "user-1"
        assert result.username == "testuser"
        assert result.groups == ["Admins"]
        assert result.roles == ["Super Admin"]
        assert result.permissions == ["hhh:contracts:read", "hhh:contracts:write"]
        assert result.rsi_handle == "TestPilot"
        assert result.rsi_verified is False
        assert result.is_user_active is True
        assert result.exp is not None
        assert result.iat is not None
        assert result.reason is None

    def test_valid_token_active_user_calls_find_by_id(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        settings: Settings,
    ) -> None:
        token = _make_access_token(settings)
        mock_repository.find_by_id.return_value = _make_user()

        service.introspect_token(token)

        mock_repository.find_by_id.assert_called_once_with("user-1")


class TestIntrospectTokenDeactivatedUser:
    def test_valid_token_deactivated_user_returns_active_false_with_reason(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        settings: Settings,
    ) -> None:
        token = _make_access_token(settings)
        mock_repository.find_by_id.return_value = _make_user(is_active=False)

        result = service.introspect_token(token)

        assert result.active is False
        assert result.sub == "user-1"
        assert result.reason == "user_deactivated"

    def test_valid_token_nonexistent_user_returns_active_false_with_reason(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        settings: Settings,
    ) -> None:
        token = _make_access_token(settings)
        mock_repository.find_by_id.return_value = None

        result = service.introspect_token(token)

        assert result.active is False
        assert result.sub == "user-1"
        assert result.reason == "user_deactivated"


class TestIntrospectTokenInvalidTokens:
    def test_expired_token_returns_active_false(
        self,
        service: AuthServiceImpl,
        settings: Settings,
    ) -> None:
        token = _make_access_token(
            settings,
            exp=datetime.now(tz=UTC) - timedelta(minutes=1),
        )

        result = service.introspect_token(token)

        assert result.active is False
        assert result.sub is None
        assert result.reason is None

    def test_invalid_signature_returns_active_false(
        self,
        service: AuthServiceImpl,
        settings: Settings,
    ) -> None:
        token = jwt.encode(
            {"sub": "user-1", "exp": datetime.now(tz=UTC) + timedelta(minutes=15)},
            "wrong-secret",
            algorithm="HS256",
        )

        result = service.introspect_token(token)

        assert result.active is False
        assert result.sub is None

    def test_malformed_token_returns_active_false(
        self,
        service: AuthServiceImpl,
    ) -> None:
        result = service.introspect_token("not-a-valid-jwt")

        assert result.active is False
        assert result.sub is None

    def test_empty_token_returns_active_false(
        self,
        service: AuthServiceImpl,
    ) -> None:
        result = service.introspect_token("")

        assert result.active is False
        assert result.sub is None

    def test_token_without_sub_returns_active_false(
        self,
        service: AuthServiceImpl,
        settings: Settings,
    ) -> None:
        token = jwt.encode(
            {"exp": datetime.now(tz=UTC) + timedelta(minutes=15)},
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )

        result = service.introspect_token(token)

        assert result.active is False
        assert result.sub is None
