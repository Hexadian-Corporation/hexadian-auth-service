from unittest.mock import MagicMock

import pytest

from src.application.ports.inbound.rbac_service import RbacService
from src.application.ports.outbound.auth_code_repository import AuthCodeRepository
from src.application.ports.outbound.group_repository import GroupRepository
from src.application.ports.outbound.refresh_token_repository import RefreshTokenRepository
from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher
from src.application.ports.outbound.user_repository import UserRepository
from src.application.services.auth_service_impl import _VERIFICATION_PREFIX, _WORD_LIST, AuthServiceImpl
from src.domain.exceptions.app_signature_exceptions import InvalidAppSignatureError
from src.domain.exceptions.user_exceptions import UserAlreadyExistsError, UserNotFoundError
from src.domain.models.group import Group
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


class TestStartVerification:
    async def test_start_verification_success(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        user = User(id="user-1", username="test")
        mock_repository.find_by_id.return_value = user

        code = await service.start_verification("user-1", "ValidHandle")

        assert code.startswith(_VERIFICATION_PREFIX)
        words_part = code[len(_VERIFICATION_PREFIX) :]
        words = words_part.split("-")
        assert len(words) == 4
        assert all(word in _WORD_LIST for word in words)
        assert user.rsi_handle == "ValidHandle"
        assert user.rsi_verification_code == code
        assert user.rsi_verified is False
        mock_repository.save.assert_called_once_with(user)

    async def test_start_verification_invalid_handle_too_short(self, service: AuthServiceImpl) -> None:
        with pytest.raises(ValueError, match="Invalid RSI handle format"):
            await service.start_verification("user-1", "ab")

    async def test_start_verification_invalid_handle_special_chars(self, service: AuthServiceImpl) -> None:
        with pytest.raises(ValueError, match="Invalid RSI handle format"):
            await service.start_verification("user-1", "bad handle!")

    async def test_start_verification_invalid_handle_too_long(self, service: AuthServiceImpl) -> None:
        with pytest.raises(ValueError, match="Invalid RSI handle format"):
            await service.start_verification("user-1", "a" * 31)

    async def test_start_verification_user_not_found(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.start_verification("nonexistent", "ValidHandle")

    async def test_start_verification_resets_verified_flag(
        self, service: AuthServiceImpl, mock_repository: MagicMock
    ) -> None:
        user = User(id="user-1", username="test", rsi_verified=True)
        mock_repository.find_by_id.return_value = user

        await service.start_verification("user-1", "NewHandle")

        assert user.rsi_verified is False

    async def test_start_verification_valid_handle_formats(
        self, service: AuthServiceImpl, mock_repository: MagicMock
    ) -> None:
        user = User(id="user-1", username="test")
        mock_repository.find_by_id.return_value = user

        for handle in ["abc", "My-Handle_123", "A" * 30]:
            code = await service.start_verification("user-1", handle)
            assert code is not None


class TestConfirmVerification:
    async def test_confirm_verification_success(
        self, service: AuthServiceImpl, mock_repository: MagicMock, mock_rsi_fetcher: MagicMock
    ) -> None:
        code = "hxn_alpha-brave-delta-ember"
        user = User(
            id="user-1",
            username="test",
            rsi_handle="TestPilot",
            rsi_verification_code=code,
        )
        mock_repository.find_by_id.return_value = user
        mock_rsi_fetcher.fetch_profile_bio.return_value = f"My bio text {code} more text"

        result = await service.confirm_verification("user-1")

        assert result is True
        assert user.rsi_verified is True
        mock_repository.save.assert_called_once_with(user)

    async def test_confirm_verification_code_not_found(
        self, service: AuthServiceImpl, mock_repository: MagicMock, mock_rsi_fetcher: MagicMock
    ) -> None:
        code = "hxn_alpha-brave-delta-ember"
        user = User(
            id="user-1",
            username="test",
            rsi_handle="TestPilot",
            rsi_verification_code=code,
        )
        mock_repository.find_by_id.return_value = user
        mock_rsi_fetcher.fetch_profile_bio.return_value = "Some bio without the code"

        result = await service.confirm_verification("user-1")

        assert result is False
        assert user.rsi_verified is False
        mock_repository.save.assert_not_called()

    async def test_confirm_verification_profile_not_found(
        self, service: AuthServiceImpl, mock_repository: MagicMock, mock_rsi_fetcher: MagicMock
    ) -> None:
        code = "hxn_alpha-brave-delta-ember"
        user = User(
            id="user-1",
            username="test",
            rsi_handle="TestPilot",
            rsi_verification_code=code,
        )
        mock_repository.find_by_id.return_value = user
        mock_rsi_fetcher.fetch_profile_bio.return_value = None

        result = await service.confirm_verification("user-1")

        assert result is False
        assert user.rsi_verified is False

    async def test_confirm_verification_user_not_found(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.confirm_verification("nonexistent")

    async def test_confirm_verification_not_started(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        user = User(id="user-1", username="test")
        mock_repository.find_by_id.return_value = user

        with pytest.raises(ValueError, match="Verification not started"):
            await service.confirm_verification("user-1")

    async def test_confirm_verification_persists_verified_to_db(
        self, service: AuthServiceImpl, mock_repository: MagicMock, mock_rsi_fetcher: MagicMock
    ) -> None:
        code = "hxn_alpha-brave-delta-ember"
        user = User(
            id="user-1",
            username="test",
            rsi_handle="TestPilot",
            rsi_verification_code=code,
            rsi_verified=False,
        )
        mock_repository.find_by_id.return_value = user
        mock_rsi_fetcher.fetch_profile_bio.return_value = f"Hello! {code} Bye!"

        await service.confirm_verification("user-1")

        saved_user = mock_repository.save.call_args[0][0]
        assert saved_user.rsi_verified is True
        assert saved_user.id == "user-1"


class TestRegister:
    async def test_register_success(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        mock_repository.find_by_username.return_value = None
        mock_repository.save.side_effect = lambda u: setattr(u, "id", "new-id") or u

        user = await service.register("newuser", "securepassword", "ValidPilot")

        assert user.username == "newuser"
        assert user.rsi_handle == "ValidPilot"
        assert not hasattr(user, "email")
        mock_repository.save.assert_called_once()

    async def test_register_duplicate_username_raises(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.find_by_username.return_value = User(id="existing", username="taken")

        with pytest.raises(UserAlreadyExistsError):
            await service.register("taken", "pw", "Pilot123")

    async def test_register_invalid_rsi_handle_raises(self, service: AuthServiceImpl) -> None:
        with pytest.raises(ValueError, match="Invalid RSI handle format"):
            await service.register("user", "pw", "ab")

    async def test_register_invalid_rsi_handle_special_chars_raises(self, service: AuthServiceImpl) -> None:
        with pytest.raises(ValueError, match="Invalid RSI handle format"):
            await service.register("user", "pw", "bad handle!")

    async def test_register_invalid_rsi_handle_too_long_raises(self, service: AuthServiceImpl) -> None:
        with pytest.raises(ValueError, match="Invalid RSI handle format"):
            await service.register("user", "pw", "a" * 31)

    async def test_register_assigns_users_group(
        self, service: AuthServiceImpl, mock_repository: MagicMock, mock_group_repository: MagicMock
    ) -> None:
        mock_repository.find_by_username.return_value = None
        mock_repository.save.side_effect = lambda u: setattr(u, "id", "new-id") or u
        mock_group_repository.find_by_name.return_value = Group(id="group-users-id", name="Users")

        user = await service.register("newuser", "pw", "ValidPilot")

        mock_group_repository.find_by_name.assert_called_once_with("Users")
        assert user.group_ids == ["group-users-id"]

    async def test_register_no_users_group_succeeds(
        self, service: AuthServiceImpl, mock_repository: MagicMock, mock_group_repository: MagicMock
    ) -> None:
        mock_repository.find_by_username.return_value = None
        mock_repository.save.side_effect = lambda u: setattr(u, "id", "new-id") or u
        mock_group_repository.find_by_name.return_value = None

        user = await service.register("newuser", "pw", "ValidPilot")

        assert user.group_ids == []


class TestRegisterWithAppId:
    async def test_valid_app_id_assigns_matching_groups(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_group_repository: MagicMock,
        settings: Settings,
    ) -> None:
        from src.application.services.app_signature import sign_app_id

        mock_repository.find_by_username.return_value = None
        mock_repository.save.side_effect = lambda u: setattr(u, "id", "new-id") or u
        users_group = Group(id="g-users", name="Users")
        hhh_group = Group(id="g-hhh", name="HHH Players", auto_assign_apps=["hhh-frontend"])
        mock_group_repository.find_by_app_id.return_value = [users_group, hhh_group]
        mock_group_repository.find_by_name.return_value = users_group

        sig = sign_app_id("hhh-frontend", settings.app_signing_secret)
        user = await service.register("newuser", "pw", "ValidPilot", app_id="hhh-frontend", app_signature=sig)

        assert "g-users" in user.group_ids
        assert "g-hhh" in user.group_ids
        assert len(user.group_ids) == 2

    async def test_valid_app_id_deduplicates_users_group(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_group_repository: MagicMock,
        settings: Settings,
    ) -> None:
        from src.application.services.app_signature import sign_app_id

        mock_repository.find_by_username.return_value = None
        mock_repository.save.side_effect = lambda u: setattr(u, "id", "new-id") or u
        users_group = Group(id="g-users", name="Users", auto_assign_apps=["hhh-frontend"])
        mock_group_repository.find_by_app_id.return_value = [users_group]
        mock_group_repository.find_by_name.return_value = users_group

        sig = sign_app_id("hhh-frontend", settings.app_signing_secret)
        user = await service.register("newuser", "pw", "ValidPilot", app_id="hhh-frontend", app_signature=sig)

        assert user.group_ids == ["g-users"]

    async def test_invalid_signature_raises_403(self, service: AuthServiceImpl, mock_repository: MagicMock) -> None:
        mock_repository.find_by_username.return_value = None

        with pytest.raises(InvalidAppSignatureError):
            await service.register("newuser", "pw", "ValidPilot", app_id="hhh-frontend", app_signature="bad-sig")

    async def test_app_id_without_signature_raises_403(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.find_by_username.return_value = None

        with pytest.raises(InvalidAppSignatureError):
            await service.register("newuser", "pw", "ValidPilot", app_id="hhh-frontend", app_signature=None)

    async def test_app_id_no_matching_groups_still_gets_users(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_group_repository: MagicMock,
        settings: Settings,
    ) -> None:
        from src.application.services.app_signature import sign_app_id

        mock_repository.find_by_username.return_value = None
        mock_repository.save.side_effect = lambda u: setattr(u, "id", "new-id") or u
        mock_group_repository.find_by_app_id.return_value = []
        mock_group_repository.find_by_name.return_value = Group(id="g-users", name="Users")

        sig = sign_app_id("unknown-app", settings.app_signing_secret)
        user = await service.register("newuser", "pw", "ValidPilot", app_id="unknown-app", app_signature=sig)

        assert user.group_ids == ["g-users"]

    async def test_no_app_id_backward_compatible(
        self,
        service: AuthServiceImpl,
        mock_repository: MagicMock,
        mock_group_repository: MagicMock,
    ) -> None:
        mock_repository.find_by_username.return_value = None
        mock_repository.save.side_effect = lambda u: setattr(u, "id", "new-id") or u
        mock_group_repository.find_by_name.return_value = Group(id="g-users", name="Users")

        user = await service.register("newuser", "pw", "ValidPilot")

        mock_group_repository.find_by_app_id.assert_not_called()
        assert user.group_ids == ["g-users"]
