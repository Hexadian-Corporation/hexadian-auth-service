from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from src.application.ports.outbound.auth_code_repository import AuthCodeRepository
from src.application.ports.outbound.group_repository import GroupRepository
from src.application.ports.outbound.refresh_token_repository import RefreshTokenRepository
from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher
from src.application.ports.outbound.user_repository import UserRepository
from src.application.services.auth_service_impl import AuthServiceImpl
from src.domain.exceptions.user_exceptions import (
    InvalidAuthCodeError,
    InvalidCredentialsError,
    InvalidRedirectUriError,
    UserNotFoundError,
)
from src.domain.models.auth_code import AuthCode
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
def settings() -> Settings:
    return Settings(jwt_secret="test-secret", jwt_expiration_minutes=15, jwt_refresh_expiration_days=7)


@pytest.fixture()
def service(
    mock_repository: MagicMock,
    mock_rsi_fetcher: MagicMock,
    mock_refresh_token_repository: MagicMock,
    mock_auth_code_repository: MagicMock,
    mock_group_repository: MagicMock,
    settings: Settings,
) -> AuthServiceImpl:
    return AuthServiceImpl(
        repository=mock_repository,
        rsi_profile_fetcher=mock_rsi_fetcher,
        refresh_token_repository=mock_refresh_token_repository,
        auth_code_repository=mock_auth_code_repository,
        group_repository=mock_group_repository,
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


class TestAuthorize:
    def test_authorize_returns_auth_code(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_auth_code_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("secret"))
        mock_repository.find_by_username.return_value = user
        mock_auth_code_repository.save.side_effect = lambda ac: ac

        result = service.authorize("testuser", "secret", "http://localhost:3000/callback", "state123")

        assert result.code != ""
        assert result.user_id == "user-1"
        assert result.redirect_uri == "http://localhost:3000/callback"
        assert result.state == "state123"
        assert result.used is False

    def test_authorize_generates_cryptographic_code(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_auth_code_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("secret"))
        mock_repository.find_by_username.return_value = user
        mock_auth_code_repository.save.side_effect = lambda ac: ac

        result = service.authorize("testuser", "secret", "http://localhost:3000/callback", "")

        # secrets.token_urlsafe(32) produces ~43 characters
        assert len(result.code) >= 40

    def test_authorize_saves_auth_code(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_auth_code_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("secret"))
        mock_repository.find_by_username.return_value = user
        mock_auth_code_repository.save.side_effect = lambda ac: ac

        service.authorize("testuser", "secret", "http://localhost:3000/callback", "state123")

        mock_auth_code_repository.save.assert_called_once()

    def test_authorize_invalid_credentials_raises(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.find_by_username.return_value = None

        with pytest.raises(InvalidCredentialsError):
            service.authorize("testuser", "wrong", "http://localhost:3000/callback", "")

    def test_authorize_wrong_password_raises(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("correct"))
        mock_repository.find_by_username.return_value = user

        with pytest.raises(InvalidCredentialsError):
            service.authorize("testuser", "wrong", "http://localhost:3000/callback", "")

    def test_authorize_invalid_redirect_uri_raises(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("secret"))
        mock_repository.find_by_username.return_value = user

        with pytest.raises(InvalidRedirectUriError):
            service.authorize("testuser", "secret", "http://evil.com/callback", "")

    def test_authorize_redirect_uri_with_path_allowed(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_auth_code_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("secret"))
        mock_repository.find_by_username.return_value = user
        mock_auth_code_repository.save.side_effect = lambda ac: ac

        result = service.authorize("testuser", "secret", "http://localhost:3000/some/path", "")

        assert result.redirect_uri == "http://localhost:3000/some/path"

    def test_authorize_empty_state_allowed(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_auth_code_repository: MagicMock,
    ) -> None:
        user = _make_user(hashed_password=AuthServiceImpl._hash_password("secret"))
        mock_repository.find_by_username.return_value = user
        mock_auth_code_repository.save.side_effect = lambda ac: ac

        result = service.authorize("testuser", "secret", "http://localhost:3000/callback", "")

        assert result.state == ""


class TestExchangeCode:
    def test_exchange_code_returns_token_response(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_auth_code_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        auth_code = AuthCode(
            id="ac-1",
            code="valid-code",
            user_id="user-1",
            redirect_uri="http://localhost:3000/callback",
            state="state123",
            expires_at=datetime.now(tz=UTC) + timedelta(seconds=30),
            used=False,
        )
        user = _make_user()
        mock_auth_code_repository.find_by_code.return_value = auth_code
        mock_repository.find_by_id.return_value = user
        mock_refresh_token_repository.save.side_effect = lambda t: t

        result = service.exchange_code("valid-code", "http://localhost:3000/callback")

        assert result.token_type == "bearer"
        assert result.expires_in == 900
        assert isinstance(result.access_token, str)
        assert isinstance(result.refresh_token, str)

    def test_exchange_code_marks_code_as_used(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_auth_code_repository: MagicMock,
        mock_refresh_token_repository: MagicMock,
    ) -> None:
        auth_code = AuthCode(
            id="ac-1",
            code="valid-code",
            user_id="user-1",
            redirect_uri="http://localhost:3000/callback",
            expires_at=datetime.now(tz=UTC) + timedelta(seconds=30),
            used=False,
        )
        user = _make_user()
        mock_auth_code_repository.find_by_code.return_value = auth_code
        mock_repository.find_by_id.return_value = user
        mock_refresh_token_repository.save.side_effect = lambda t: t

        service.exchange_code("valid-code", "http://localhost:3000/callback")

        mock_auth_code_repository.mark_used.assert_called_once_with("valid-code")

    def test_exchange_code_not_found_raises(
        self,
        service: AuthServiceImpl,
        mock_auth_code_repository: MagicMock,
    ) -> None:
        mock_auth_code_repository.find_by_code.return_value = None

        with pytest.raises(InvalidAuthCodeError):
            service.exchange_code("nonexistent", "http://localhost:3000/callback")

    def test_exchange_code_already_used_raises(
        self,
        service: AuthServiceImpl,
        mock_auth_code_repository: MagicMock,
    ) -> None:
        auth_code = AuthCode(
            id="ac-1",
            code="used-code",
            user_id="user-1",
            redirect_uri="http://localhost:3000/callback",
            expires_at=datetime.now(tz=UTC) + timedelta(seconds=30),
            used=True,
        )
        mock_auth_code_repository.find_by_code.return_value = auth_code

        with pytest.raises(InvalidAuthCodeError, match="already been used"):
            service.exchange_code("used-code", "http://localhost:3000/callback")

    def test_exchange_code_expired_raises(
        self,
        service: AuthServiceImpl,
        mock_auth_code_repository: MagicMock,
    ) -> None:
        auth_code = AuthCode(
            id="ac-1",
            code="expired-code",
            user_id="user-1",
            redirect_uri="http://localhost:3000/callback",
            expires_at=datetime.now(tz=UTC) - timedelta(seconds=10),
            used=False,
        )
        mock_auth_code_repository.find_by_code.return_value = auth_code

        with pytest.raises(InvalidAuthCodeError, match="expired"):
            service.exchange_code("expired-code", "http://localhost:3000/callback")

    def test_exchange_code_redirect_uri_mismatch_raises(
        self,
        service: AuthServiceImpl,
        mock_auth_code_repository: MagicMock,
    ) -> None:
        auth_code = AuthCode(
            id="ac-1",
            code="valid-code",
            user_id="user-1",
            redirect_uri="http://localhost:3000/callback",
            expires_at=datetime.now(tz=UTC) + timedelta(seconds=30),
            used=False,
        )
        mock_auth_code_repository.find_by_code.return_value = auth_code

        with pytest.raises(InvalidAuthCodeError, match="mismatch"):
            service.exchange_code("valid-code", "http://localhost:3001/callback")

    def test_exchange_code_user_not_found_raises(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_auth_code_repository: MagicMock,
    ) -> None:
        auth_code = AuthCode(
            id="ac-1",
            code="valid-code",
            user_id="deleted-user",
            redirect_uri="http://localhost:3000/callback",
            expires_at=datetime.now(tz=UTC) + timedelta(seconds=30),
            used=False,
        )
        mock_auth_code_repository.find_by_code.return_value = auth_code
        mock_repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            service.exchange_code("valid-code", "http://localhost:3000/callback")
