from unittest.mock import MagicMock

import pytest

from src.application.ports.inbound.rbac_service import RbacService
from src.application.ports.outbound.auth_code_repository import AuthCodeRepository
from src.application.ports.outbound.group_repository import GroupRepository
from src.application.ports.outbound.refresh_token_repository import RefreshTokenRepository
from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher
from src.application.ports.outbound.user_repository import UserRepository
from src.application.services.auth_service_impl import AuthServiceImpl
from src.domain.exceptions.user_exceptions import (
    InvalidPasswordError,
    UserNotFoundError,
)
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


class TestChangePassword:
    async def test_change_password_success(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("old-secret"))
        mock_repository.find_by_id.return_value = user
        mock_repository.save.side_effect = lambda u: u

        await service.change_password("user-1", "old-secret", "new-secret-password")

        mock_repository.save.assert_called_once()
        saved_user = mock_repository.save.call_args[0][0]
        assert AuthServiceImpl._verify_password("new-secret-password", saved_user.hashed_password)

    async def test_change_password_revokes_all_refresh_tokens(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("old-secret"))
        mock_repository.find_by_id.return_value = user
        mock_repository.save.side_effect = lambda u: u

        await service.change_password("user-1", "old-secret", "new-secret-password")

        mock_refresh_token_repository.revoke_all_for_user.assert_called_once_with("user-1")

    async def test_change_password_wrong_old_password_raises(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("correct"))
        mock_repository.find_by_id.return_value = user

        with pytest.raises(InvalidPasswordError, match="Old password is incorrect"):
            await service.change_password("user-1", "wrong", "new-secret-password")

    async def test_change_password_weak_new_password_raises(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("old-secret"))
        mock_repository.find_by_id.return_value = user

        with pytest.raises(InvalidPasswordError, match="at least 8 characters"):
            await service.change_password("user-1", "old-secret", "short")

    async def test_change_password_user_not_found_raises(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.change_password("nonexistent", "old", "new-secret-password")


class TestResetPassword:
    async def test_reset_password_success(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("old"))
        mock_repository.find_by_id.return_value = user
        mock_repository.save.side_effect = lambda u: u

        await service.reset_password("user-1", "new-admin-password")

        mock_repository.save.assert_called_once()
        saved_user = mock_repository.save.call_args[0][0]
        assert AuthServiceImpl._verify_password("new-admin-password", saved_user.hashed_password)

    async def test_reset_password_revokes_all_refresh_tokens(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("old"))
        mock_repository.find_by_id.return_value = user
        mock_repository.save.side_effect = lambda u: u

        await service.reset_password("user-1", "new-admin-password")

        mock_refresh_token_repository.revoke_all_for_user.assert_called_once_with("user-1")

    async def test_reset_password_weak_new_password_raises(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("old"))
        mock_repository.find_by_id.return_value = user

        with pytest.raises(InvalidPasswordError, match="at least 8 characters"):
            await service.reset_password("user-1", "short")

    async def test_reset_password_user_not_found_raises(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.reset_password("nonexistent", "new-admin-password")
