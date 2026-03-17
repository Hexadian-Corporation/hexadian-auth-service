from unittest.mock import MagicMock

import pytest

from src.application.ports.inbound.rbac_service import RbacService
from src.application.ports.outbound.auth_code_repository import AuthCodeRepository
from src.application.ports.outbound.group_repository import GroupRepository
from src.application.ports.outbound.refresh_token_repository import RefreshTokenRepository
from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher
from src.application.ports.outbound.user_repository import UserRepository
from src.application.services.auth_service_impl import AuthServiceImpl, _VERIFICATION_PREFIX, _WORD_LIST
from src.domain.exceptions.user_exceptions import (
    RsiHandleMismatchError,
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
        "hashed_password": AuthServiceImpl._hash_password("old-secret"),
        "rsi_handle": "TestPilot",
        "rsi_verified": False,
    }
    defaults.update(overrides)
    return User(**defaults)


class TestForgotPassword:
    def test_forgot_password_success(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        user = _make_user()
        mock_repository.find_by_username.return_value = user

        code = service.forgot_password("testuser", "TestPilot")

        assert code.startswith(_VERIFICATION_PREFIX)
        words_part = code[len(_VERIFICATION_PREFIX) :]
        words = words_part.split("-")
        assert len(words) == 6
        assert all(word in _WORD_LIST for word in words)
        assert user.rsi_verification_code == code
        mock_repository.save.assert_called_once_with(user)

    def test_forgot_password_user_not_found(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        mock_repository.find_by_username.return_value = None

        with pytest.raises(UserNotFoundError):
            service.forgot_password("nonexistent", "SomeHandle")

    def test_forgot_password_rsi_handle_mismatch(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        user = _make_user(rsi_handle="ActualHandle")
        mock_repository.find_by_username.return_value = user

        with pytest.raises(RsiHandleMismatchError):
            service.forgot_password("testuser", "WrongHandle")

    def test_forgot_password_works_for_unverified_user(
        self, service: AuthServiceImpl, mock_repository: MagicMock
    ) -> None:
        user = _make_user(rsi_verified=False)
        mock_repository.find_by_username.return_value = user

        code = service.forgot_password("testuser", "TestPilot")

        assert code is not None
        mock_repository.save.assert_called_once()


class TestConfirmForgotPassword:
    def test_confirm_forgot_password_success(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_rsi_fetcher: MagicMock,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        code = "Hexadian account validation code: alpha-brave-delta-ember-frost-ocean"
        user = _make_user(rsi_verification_code=code)
        mock_repository.find_by_username.return_value = user
        mock_rsi_fetcher.fetch_profile_bio.return_value = f"My bio {code} end"
        mock_repository.save.side_effect = lambda u: u

        service.confirm_forgot_password("testuser", "TestPilot", "new-secure-password")

        mock_repository.save.assert_called_once()
        saved_user = mock_repository.save.call_args[0][0]
        assert AuthServiceImpl._verify_password("new-secure-password", saved_user.hashed_password)
        assert saved_user.rsi_verification_code is None

    def test_confirm_forgot_password_revokes_all_refresh_tokens(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_rsi_fetcher: MagicMock,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        code = "Hexadian account validation code: alpha-brave-delta-ember-frost-ocean"
        user = _make_user(rsi_verification_code=code)
        mock_repository.find_by_username.return_value = user
        mock_rsi_fetcher.fetch_profile_bio.return_value = f"My bio {code} end"
        mock_repository.save.side_effect = lambda u: u

        service.confirm_forgot_password("testuser", "TestPilot", "new-secure-password")

        mock_refresh_token_repository.revoke_all_for_user.assert_called_once_with("user-1")

    def test_confirm_forgot_password_user_not_found(
        self, service: AuthServiceImpl, mock_repository: MagicMock
    ) -> None:
        mock_repository.find_by_username.return_value = None

        with pytest.raises(UserNotFoundError):
            service.confirm_forgot_password("nonexistent", "Handle", "new-password-secure")

    def test_confirm_forgot_password_rsi_handle_mismatch(
        self, service: AuthServiceImpl, mock_repository: MagicMock
    ) -> None:
        user = _make_user(rsi_handle="ActualHandle", rsi_verification_code="some-code")
        mock_repository.find_by_username.return_value = user

        with pytest.raises(RsiHandleMismatchError):
            service.confirm_forgot_password("testuser", "WrongHandle", "new-password-secure")

    def test_confirm_forgot_password_no_verification_code(
        self, service: AuthServiceImpl, mock_repository: MagicMock
    ) -> None:
        user = _make_user(rsi_verification_code=None)
        mock_repository.find_by_username.return_value = user

        with pytest.raises(ValueError, match="No verification code set"):
            service.confirm_forgot_password("testuser", "TestPilot", "new-password-secure")

    def test_confirm_forgot_password_code_not_in_bio(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_rsi_fetcher: MagicMock,
    ) -> None:
        code = "Hexadian account validation code: alpha-brave-delta-ember-frost-ocean"
        user = _make_user(rsi_verification_code=code)
        mock_repository.find_by_username.return_value = user
        mock_rsi_fetcher.fetch_profile_bio.return_value = "Bio without the code"

        with pytest.raises(ValueError, match="Verification code not found"):
            service.confirm_forgot_password("testuser", "TestPilot", "new-password-secure")

    def test_confirm_forgot_password_profile_not_found(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_rsi_fetcher: MagicMock,
    ) -> None:
        code = "Hexadian account validation code: alpha-brave-delta-ember-frost-ocean"
        user = _make_user(rsi_verification_code=code)
        mock_repository.find_by_username.return_value = user
        mock_rsi_fetcher.fetch_profile_bio.return_value = None

        with pytest.raises(ValueError, match="Verification code not found"):
            service.confirm_forgot_password("testuser", "TestPilot", "new-password-secure")

    def test_confirm_forgot_password_clears_verification_code(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_rsi_fetcher: MagicMock,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        code = "Hexadian account validation code: alpha-brave-delta-ember-frost-ocean"
        user = _make_user(rsi_verification_code=code)
        mock_repository.find_by_username.return_value = user
        mock_rsi_fetcher.fetch_profile_bio.return_value = f"Hello {code} world"
        mock_repository.save.side_effect = lambda u: u

        service.confirm_forgot_password("testuser", "TestPilot", "new-secure-password")

        saved_user = mock_repository.save.call_args[0][0]
        assert saved_user.rsi_verification_code is None
