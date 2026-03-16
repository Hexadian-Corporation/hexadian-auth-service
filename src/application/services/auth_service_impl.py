import hashlib
import re
import secrets

from src.application.ports.inbound.auth_service import AuthService
from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher
from src.application.ports.outbound.user_repository import UserRepository
from src.domain.exceptions.user_exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.domain.models.user import User

_RSI_HANDLE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,30}$")

_VERIFICATION_PREFIX = "Hexadian account validation code: "

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

_NUM_WORDS = 6


def _generate_verification_code() -> str:
    words = [secrets.choice(_WORD_LIST) for _ in range(_NUM_WORDS)]
    return _VERIFICATION_PREFIX + "-".join(words)


class AuthServiceImpl(AuthService):
    def __init__(self, repository: UserRepository, rsi_profile_fetcher: RsiProfileFetcher) -> None:
        self._repository = repository
        self._rsi_profile_fetcher = rsi_profile_fetcher

    def register(self, username: str, email: str, password: str) -> User:
        if self._repository.find_by_username(username) is not None:
            raise UserAlreadyExistsError(username)
        hashed = self._hash_password(password)
        user = User(username=username, email=email, hashed_password=hashed)
        return self._repository.save(user)

    def authenticate(self, username: str, password: str) -> str:
        user = self._repository.find_by_username(username)
        if user is None or not self._verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
        # TODO: Generate JWT token
        return f"token-{user.id}"

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
