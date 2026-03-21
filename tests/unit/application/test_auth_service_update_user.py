from unittest.mock import MagicMock

import pytest

from src.application.ports.inbound.rbac_service import RbacService
from src.application.ports.outbound.auth_code_repository import AuthCodeRepository
from src.application.ports.outbound.group_repository import GroupRepository
from src.application.ports.outbound.refresh_token_repository import RefreshTokenRepository
from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher
from src.application.ports.outbound.user_repository import UserRepository
from src.application.services.auth_service_impl import AuthServiceImpl
from src.domain.exceptions.user_exceptions import UserAlreadyExistsError, UserNotFoundError
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
    return Settings(jwt_secret="test-secret")


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


class TestUpdateUserUsername:
    async def test_update_username_success(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        updated_user = User(id="user-1", username="newname", rsi_handle="Pilot")
        mock_repository.find_by_username.return_value = None
        mock_repository.update.return_value = updated_user

        result = await service.update_user("user-1", {"username": "newname"})

        assert result.username == "newname"
        mock_repository.update.assert_called_once_with("user-1", {"username": "newname"})

    async def test_update_username_same_user_keeps_own(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        existing = User(id="user-1", username="samename")
        mock_repository.find_by_username.return_value = existing
        updated_user = User(id="user-1", username="samename")
        mock_repository.update.return_value = updated_user

        result = await service.update_user("user-1", {"username": "samename"})

        assert result.username == "samename"
        mock_repository.update.assert_called_once()

    async def test_update_username_duplicate_raises_409(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        other_user = User(id="user-2", username="taken")
        mock_repository.find_by_username.return_value = other_user

        with pytest.raises(UserAlreadyExistsError):
            await service.update_user("user-1", {"username": "taken"})


class TestUpdateUserRsiHandle:
    async def test_update_rsi_handle_resets_verification(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        updated_user = User(
            id="user-1",
            username="test",
            rsi_handle="NewHandle",
            rsi_verified=False,
            rsi_verification_code=None,
        )
        mock_repository.update.return_value = updated_user

        result = await service.update_user("user-1", {"rsi_handle": "NewHandle"})

        assert result.rsi_verified is False
        mock_repository.update.assert_called_once_with(
            "user-1",
            {"rsi_handle": "NewHandle", "rsi_verified": False, "rsi_verification_code": None},
        )

    async def test_update_rsi_handle_invalid_format_raises(self, service: AuthServiceImpl) -> None:
        with pytest.raises(ValueError, match="Invalid RSI handle format"):
            await service.update_user("user-1", {"rsi_handle": "ab"})

    async def test_update_rsi_handle_special_chars_raises(self, service: AuthServiceImpl) -> None:
        with pytest.raises(ValueError, match="Invalid RSI handle format"):
            await service.update_user("user-1", {"rsi_handle": "bad handle!"})

    async def test_update_rsi_handle_too_long_raises(self, service: AuthServiceImpl) -> None:
        with pytest.raises(ValueError, match="Invalid RSI handle format"):
            await service.update_user("user-1", {"rsi_handle": "a" * 31})


class TestUpdateUserGeneral:
    async def test_update_user_not_found_raises(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        mock_repository.find_by_username.return_value = None
        mock_repository.update.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.update_user("nonexistent", {"username": "newname"})

    async def test_update_disallowed_field_raises(self, service: AuthServiceImpl) -> None:
        with pytest.raises(ValueError, match="Field not editable"):
            await service.update_user("user-1", {"hashed_password": "evil"})

    async def test_update_empty_dict_returns_user(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        user = User(id="user-1", username="test")
        mock_repository.find_by_id.return_value = user

        result = await service.update_user("user-1", {})

        assert result.id == "user-1"
        mock_repository.update.assert_not_called()

    async def test_update_both_fields(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        updated_user = User(
            id="user-1",
            username="newname",
            rsi_handle="NewHandle",
            rsi_verified=False,
        )
        mock_repository.find_by_username.return_value = None
        mock_repository.update.return_value = updated_user

        result = await service.update_user("user-1", {"username": "newname", "rsi_handle": "NewHandle"})

        assert result.username == "newname"
        assert result.rsi_handle == "NewHandle"
        mock_repository.update.assert_called_once_with(
            "user-1",
            {
                "rsi_handle": "NewHandle",
                "rsi_verified": False,
                "rsi_verification_code": None,
                "username": "newname",
            },
        )
