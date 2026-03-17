import hashlib
import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

import jwt

from src.application.ports.inbound.auth_service import AuthService
from src.application.ports.inbound.rbac_service import RbacService
from src.application.ports.outbound.auth_code_repository import AuthCodeRepository
from src.application.ports.outbound.group_repository import GroupRepository
from src.application.ports.outbound.refresh_token_repository import RefreshTokenRepository
from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher
from src.application.ports.outbound.user_repository import UserRepository
from src.application.services.app_signature import verify_app_signature
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
from src.domain.models.auth_code import AuthCode
from src.domain.models.refresh_token import RefreshToken
from src.domain.models.token_response import TokenResponse
from src.domain.models.user import User
from src.infrastructure.config.settings import Settings

_RSI_HANDLE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,30}$")

_VERIFICATION_PREFIX = "hxn_"

# fmt: off
_WORD_LIST: list[str] = [
    "alpha", "anchor", "anvil", "apple", "arrow", "atlas", "aurora", "badge",
    "baker", "basin", "beach", "bell", "berry", "blade", "blaze", "bloom",
    "board", "bonus", "brave", "brick", "bridge", "bright", "brook", "cabin",
    "camel", "candy", "cargo", "cedar", "chain", "chalk", "chase", "chess",
    "chief", "cider", "civil", "claim", "cliff", "climb", "clock", "cloud",
    "coast", "cobra", "comet", "coral", "crane", "creek", "crisp", "cross",
    "crown", "curve", "cycle", "dance", "delta", "diary", "dodge", "dove",
    "draft", "dream", "drift", "drive", "dusk", "eagle", "earth", "ember",
    "entry", "epoch", "event", "extra", "fable", "fairy", "feast", "fence",
    "ferry", "field", "flame", "flash", "fleet", "flint", "float", "flood",
    "flute", "focus", "forge", "forte", "forum", "frost", "fruit", "gale",
    "garden", "ghost", "giant", "glade", "gleam", "globe", "glory", "grain",
    "grape", "grasp", "green", "grove", "guard", "guide", "gypsy", "habit",
    "harbor", "haven", "heart", "hedge", "heron", "honey", "honor", "horse",
    "house", "ivory", "jewel", "jolly", "judge", "juice", "karma", "kayak",
    "knack", "knelt", "knife", "knock", "lance", "larch", "laser", "latch",
    "lemon", "level", "light", "lilac", "linen", "lodge", "lunar", "magic",
    "maple", "marsh", "medal", "melon", "mercy", "merit", "mirth", "model",
    "moose", "mount", "music", "noble", "north", "novel", "oasis", "ocean",
    "olive", "onset", "opera", "orbit", "order", "outer", "oxide", "ozone",
    "panda", "panel", "pearl", "penny", "piano", "pilot", "pixel", "plain",
    "plant", "plaza", "plumb", "plume", "point", "polar", "pond", "pouch",
    "prime", "prism", "proud", "pulse", "quail", "quest", "quiet", "quilt",
    "radar", "rapid", "raven", "realm", "relay", "ridge", "river", "robin",
    "royal", "ruby", "saint", "scale", "scene", "scout", "serif", "shade",
    "sharp", "shell", "shine", "shore", "siege", "sigma", "silk", "skill",
    "slate", "slope", "smart", "solar", "south", "space", "spark", "spear",
    "spice", "spine", "spoke", "spray", "stage", "stamp", "steam", "steel",
    "stern", "stone", "storm", "stove", "straw", "sugar", "suite", "surge",
    "swift", "sword", "table", "tango", "tempo", "thorn", "tiger", "toast",
    "token", "torch", "tower", "trace", "trail", "trend", "tribe", "trout",
    "tulip", "ultra", "unity", "urban", "valve", "vault", "verse", "vigor",
    "villa", "viola", "vivid", "vocal", "watch", "water", "wheat", "wheel",
    "world", "yacht", "yield", "zebra", "zephyr",
]
# fmt: on

_NUM_WORDS = 4


def _generate_verification_code() -> str:
    words = [secrets.choice(_WORD_LIST) for _ in range(_NUM_WORDS)]
    return _VERIFICATION_PREFIX + "-".join(words)


class AuthServiceImpl(AuthService):
    def __init__(
        self,
        repository: UserRepository,
        rsi_profile_fetcher: RsiProfileFetcher,
        refresh_token_repository: RefreshTokenRepository,
        auth_code_repository: AuthCodeRepository,
        group_repository: GroupRepository,
        rbac_service: RbacService,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._rsi_profile_fetcher = rsi_profile_fetcher
        self._refresh_token_repository = refresh_token_repository
        self._auth_code_repository = auth_code_repository
        self._group_repository = group_repository
        self._rbac_service = rbac_service
        self._settings = settings

    def register(
        self, username: str, password: str, rsi_handle: str, app_id: str | None = None, app_signature: str | None = None
    ) -> User:
        if not _RSI_HANDLE_PATTERN.match(rsi_handle):
            raise ValueError(f"Invalid RSI handle format: {rsi_handle}")
        if app_id is not None and (
            app_signature is None or not verify_app_signature(app_id, app_signature, self._settings.app_signing_secret)
        ):
            raise InvalidAppSignatureError()
        if self._repository.find_by_username(username) is not None:
            raise UserAlreadyExistsError(username)
        hashed = self._hash_password(password)
        user = User(username=username, hashed_password=hashed, rsi_handle=rsi_handle)

        group_ids: list[str] = []
        seen_ids: set[str] = set()

        if app_id is not None:
            matched_groups = self._group_repository.find_by_app_id(app_id)
            for g in matched_groups:
                if g.id not in seen_ids:
                    seen_ids.add(g.id)
                    group_ids.append(g.id)

        users_group = self._group_repository.find_by_name("Users")
        if users_group is not None and users_group.id not in seen_ids:
            seen_ids.add(users_group.id)
            group_ids.append(users_group.id)

        user.group_ids = group_ids
        return self._repository.save(user)

    def authenticate(self, username: str, password: str) -> TokenResponse:
        user = self._repository.find_by_username(username)
        if user is None or not self._verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
        return self._create_token_pair(user)

    def refresh_token(self, token: str) -> TokenResponse:
        existing = self._refresh_token_repository.find_by_token(token)
        if existing is None or existing.revoked:
            raise RefreshTokenNotFoundError(token)
        if existing.expires_at < datetime.now(tz=UTC):
            raise RefreshTokenNotFoundError(token)

        user = self._repository.find_by_id(existing.user_id)
        if user is None:
            raise UserNotFoundError(existing.user_id)

        self._refresh_token_repository.revoke(token)
        return self._create_token_pair(user)

    def revoke_token(self, token: str) -> None:
        existing = self._refresh_token_repository.find_by_token(token)
        if existing is None:
            raise RefreshTokenNotFoundError(token)
        self._refresh_token_repository.revoke(token)

    def _generate_access_token(self, user: User) -> str:
        now = datetime.now(tz=UTC)
        claims = self._rbac_service.resolve_rbac_claims(user.id)
        payload = {
            "sub": user.id,
            "username": user.username,
            "groups": claims.groups,
            "roles": claims.roles,
            "permissions": claims.permissions,
            "rsi_handle": user.rsi_handle,
            "rsi_verified": user.rsi_verified,
            "iat": now,
            "exp": now + timedelta(minutes=self._settings.jwt_expiration_minutes),
        }
        return jwt.encode(payload, self._settings.jwt_secret, algorithm=self._settings.jwt_algorithm)

    def _generate_refresh_token(self, user: User) -> RefreshToken:
        return RefreshToken(
            user_id=user.id,
            token=str(uuid.uuid4()),
            expires_at=datetime.now(tz=UTC) + timedelta(days=self._settings.jwt_refresh_expiration_days),
        )

    def _create_token_pair(self, user: User) -> TokenResponse:
        access_token = self._generate_access_token(user)
        refresh = self._generate_refresh_token(user)
        self._refresh_token_repository.save(refresh)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh.token,
            expires_in=self._settings.jwt_expiration_minutes * 60,
        )

    def get_user(self, user_id: str) -> User:
        user = self._repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def list_users(self) -> list[User]:
        return self._repository.find_all()

    def delete_user(self, user_id: str) -> None:
        if not self._repository.delete(user_id):
            raise UserNotFoundError(user_id)

    _ALLOWED_UPDATE_FIELDS = {"username", "rsi_handle"}

    def update_user(self, user_id: str, updates: dict) -> User:
        fields: dict = {}
        for key in updates:
            if key not in self._ALLOWED_UPDATE_FIELDS:
                raise ValueError(f"Field not editable: {key}")

        if "rsi_handle" in updates:
            rsi_handle = updates["rsi_handle"]
            if not _RSI_HANDLE_PATTERN.match(rsi_handle):
                raise ValueError(f"Invalid RSI handle format: {rsi_handle}")
            fields["rsi_handle"] = rsi_handle
            fields["rsi_verified"] = False
            fields["rsi_verification_code"] = None

        if "username" in updates:
            username = updates["username"]
            existing = self._repository.find_by_username(username)
            if existing is not None and existing.id != user_id:
                raise UserAlreadyExistsError(username)
            fields["username"] = username

        if not fields:
            return self.get_user(user_id)

        user = self._repository.update(user_id, fields)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
        return f"{salt}:{hashed.hex()}"

    @staticmethod
    def _verify_password(password: str, hashed_password: str) -> bool:
        salt, expected_hash = hashed_password.split(":")
        actual_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
        return secrets.compare_digest(actual_hash.hex(), expected_hash)

    def start_verification(self, user_id: str, rsi_handle: str) -> str:
        if not _RSI_HANDLE_PATTERN.match(rsi_handle):
            raise ValueError(f"Invalid RSI handle format: {rsi_handle}")

        user = self._repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        code = _generate_verification_code()
        user.rsi_handle = rsi_handle
        user.rsi_verification_code = code
        user.rsi_verified = False
        self._repository.save(user)
        return code

    def confirm_verification(self, user_id: str) -> bool:
        user = self._repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        if not user.rsi_handle or not user.rsi_verification_code:
            raise ValueError("Verification not started. Call start_verification first.")

        bio = self._rsi_profile_fetcher.fetch_profile_bio(user.rsi_handle)
        if bio is not None and user.rsi_verification_code in bio:
            user.rsi_verified = True
            self._repository.save(user)
            return True
        return False

    def authorize(self, username: str, password: str, redirect_uri: str, state: str) -> AuthCode:
        # TODO: Consider PKCE for enhanced security
        user = self._repository.find_by_username(username)
        if user is None or not self._verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        self._validate_redirect_uri(redirect_uri)

        code = secrets.token_urlsafe(32)
        auth_code = AuthCode(
            code=code,
            user_id=user.id,
            redirect_uri=redirect_uri,
            state=state,
        )
        return self._auth_code_repository.save(auth_code)

    def exchange_code(self, code: str, redirect_uri: str) -> TokenResponse:
        # TODO: Consider PKCE for enhanced security
        auth_code = self._auth_code_repository.find_by_code(code)
        if auth_code is None:
            raise InvalidAuthCodeError()
        if auth_code.used:
            raise InvalidAuthCodeError("Authorization code has already been used")
        if auth_code.expires_at < datetime.now(tz=UTC):
            raise InvalidAuthCodeError("Authorization code has expired")
        if auth_code.redirect_uri != redirect_uri:
            raise InvalidAuthCodeError("Redirect URI mismatch")

        self._auth_code_repository.mark_used(code)

        user = self._repository.find_by_id(auth_code.user_id)
        if user is None:
            raise UserNotFoundError(auth_code.user_id)

        return self._create_token_pair(user)

    def _validate_redirect_uri(self, redirect_uri: str) -> None:
        parsed = urlparse(redirect_uri)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._settings.allowed_redirect_origins:
            raise InvalidRedirectUriError(redirect_uri)

    def change_password(self, user_id: str, old_password: str, new_password: str) -> None:
        user = self._repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        if not self._verify_password(old_password, user.hashed_password):
            raise InvalidPasswordError("Old password is incorrect")
        if len(new_password) < 8:
            raise InvalidPasswordError("New password must be at least 8 characters")
        user.hashed_password = self._hash_password(new_password)
        self._repository.save(user)
        self._refresh_token_repository.revoke_all_for_user(user_id)

    def reset_password(self, user_id: str, new_password: str) -> None:
        user = self._repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        if len(new_password) < 8:
            raise InvalidPasswordError("New password must be at least 8 characters")
        user.hashed_password = self._hash_password(new_password)
        self._repository.save(user)
        self._refresh_token_repository.revoke_all_for_user(user_id)
