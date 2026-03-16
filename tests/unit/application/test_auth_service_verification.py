from unittest.mock import MagicMock

import pytest

from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher
from src.application.ports.outbound.user_repository import UserRepository
from src.application.services.auth_service_impl import _VERIFICATION_PREFIX, _WORD_LIST, AuthServiceImpl
from src.domain.exceptions.user_exceptions import UserNotFoundError
from src.domain.models.user import User


@pytest.fixture()
def mock_repository() -> MagicMock:
    return MagicMock(spec=UserRepository)


@pytest.fixture()
def mock_rsi_fetcher() -> MagicMock:
    return MagicMock(spec=RsiProfileFetcher)


@pytest.fixture()
def service(mock_repository: MagicMock, mock_rsi_fetcher: MagicMock) -> AuthServiceImpl:
    return AuthServiceImpl(repository=mock_repository, rsi_profile_fetcher=mock_rsi_fetcher)


class TestStartVerification:
    def test_start_verification_success(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        user = User(id="user-1", username="test", email="test@example.com")
        mock_repository.find_by_id.return_value = user

        code = service.start_verification("user-1", "ValidHandle")

        assert code.startswith(_VERIFICATION_PREFIX)
        words_part = code[len(_VERIFICATION_PREFIX) :]
        words = words_part.split("-")
        assert len(words) == 6
        assert all(word in _WORD_LIST for word in words)
        assert user.rsi_handle == "ValidHandle"
        assert user.rsi_verification_code == code
        assert user.rsi_verified is False
        mock_repository.save.assert_called_once_with(user)

    def test_start_verification_invalid_handle_too_short(self, service: AuthServiceImpl) -> None:
        with pytest.raises(ValueError, match="Invalid RSI handle format"):
            service.start_verification("user-1", "ab")

    def test_start_verification_invalid_handle_special_chars(self, service: AuthServiceImpl) -> None:
        with pytest.raises(ValueError, match="Invalid RSI handle format"):
            service.start_verification("user-1", "bad handle!")

    def test_start_verification_invalid_handle_too_long(self, service: AuthServiceImpl) -> None:
        with pytest.raises(ValueError, match="Invalid RSI handle format"):
            service.start_verification("user-1", "a" * 31)

    def test_start_verification_user_not_found(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        mock_repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            service.start_verification("nonexistent", "ValidHandle")

    def test_start_verification_resets_verified_flag(
        self, service: AuthServiceImpl, mock_repository: MagicMock
    ) -> None:
        user = User(id="user-1", username="test", email="test@example.com", rsi_verified=True)
        mock_repository.find_by_id.return_value = user

        service.start_verification("user-1", "NewHandle")

        assert user.rsi_verified is False

    def test_start_verification_valid_handle_formats(
        self, service: AuthServiceImpl, mock_repository: MagicMock
    ) -> None:
        user = User(id="user-1", username="test", email="test@example.com")
        mock_repository.find_by_id.return_value = user

        for handle in ["abc", "My-Handle_123", "A" * 30]:
            code = service.start_verification("user-1", handle)
            assert code is not None


class TestConfirmVerification:
    def test_confirm_verification_success(
        self, service: AuthServiceImpl, mock_repository: MagicMock, mock_rsi_fetcher: MagicMock
    ) -> None:
        code = "Hexadian account validation code: alpha-brave-delta-ember-frost-ocean"
        user = User(
            id="user-1",
            username="test",
            email="test@example.com",
            rsi_handle="TestPilot",
            rsi_verification_code=code,
        )
        mock_repository.find_by_id.return_value = user
        mock_rsi_fetcher.fetch_profile_bio.return_value = f"My bio text {code} more text"

        result = service.confirm_verification("user-1")

        assert result is True
        assert user.rsi_verified is True
        mock_repository.save.assert_called_once_with(user)

    def test_confirm_verification_code_not_found(
        self, service: AuthServiceImpl, mock_repository: MagicMock, mock_rsi_fetcher: MagicMock
    ) -> None:
        code = "Hexadian account validation code: alpha-brave-delta-ember-frost-ocean"
        user = User(
            id="user-1",
            username="test",
            email="test@example.com",
            rsi_handle="TestPilot",
            rsi_verification_code=code,
        )
        mock_repository.find_by_id.return_value = user
        mock_rsi_fetcher.fetch_profile_bio.return_value = "Some bio without the code"

        result = service.confirm_verification("user-1")

        assert result is False
        assert user.rsi_verified is False
        mock_repository.save.assert_not_called()

    def test_confirm_verification_profile_not_found(
        self, service: AuthServiceImpl, mock_repository: MagicMock, mock_rsi_fetcher: MagicMock
    ) -> None:
        code = "Hexadian account validation code: alpha-brave-delta-ember-frost-ocean"
        user = User(
            id="user-1",
            username="test",
            email="test@example.com",
            rsi_handle="TestPilot",
            rsi_verification_code=code,
        )
        mock_repository.find_by_id.return_value = user
        mock_rsi_fetcher.fetch_profile_bio.return_value = None

        result = service.confirm_verification("user-1")

        assert result is False
        assert user.rsi_verified is False

    def test_confirm_verification_user_not_found(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        mock_repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            service.confirm_verification("nonexistent")

    def test_confirm_verification_not_started(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        user = User(id="user-1", username="test", email="test@example.com")
        mock_repository.find_by_id.return_value = user

        with pytest.raises(ValueError, match="Verification not started"):
            service.confirm_verification("user-1")

    def test_confirm_verification_persists_verified_to_db(
        self, service: AuthServiceImpl, mock_repository: MagicMock, mock_rsi_fetcher: MagicMock
    ) -> None:
        code = "Hexadian account validation code: alpha-brave-delta-ember-frost-ocean"
        user = User(
            id="user-1",
            username="test",
            email="test@example.com",
            rsi_handle="TestPilot",
            rsi_verification_code=code,
            rsi_verified=False,
        )
        mock_repository.find_by_id.return_value = user
        mock_rsi_fetcher.fetch_profile_bio.return_value = f"Hello! {code} Bye!"

        service.confirm_verification("user-1")

        saved_user = mock_repository.save.call_args[0][0]
        assert saved_user.rsi_verified is True
        assert saved_user.id == "user-1"
