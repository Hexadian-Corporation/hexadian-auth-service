from abc import ABC, abstractmethod

from src.domain.models.auth_code import AuthCode
from src.domain.models.introspection_result import IntrospectionResult
from src.domain.models.token_response import TokenResponse
from src.domain.models.user import User


class AuthService(ABC):
    @abstractmethod
    async def register(
        self, username: str, password: str, rsi_handle: str, app_id: str | None = None, app_signature: str | None = None
    ) -> User: ...

    @abstractmethod
    async def authenticate(self, username: str, password: str) -> TokenResponse: ...

    @abstractmethod
    async def refresh_token(self, token: str) -> TokenResponse: ...

    @abstractmethod
    async def revoke_token(self, token: str) -> None: ...

    @abstractmethod
    async def get_user(self, user_id: str) -> User: ...

    @abstractmethod
    async def list_users(self) -> list[User]: ...

    @abstractmethod
    async def delete_user(self, user_id: str) -> None: ...

    @abstractmethod
    async def start_verification(self, user_id: str, rsi_handle: str) -> str:
        """Generate a verification code and store it on the user. Returns the code."""
        ...

    @abstractmethod
    async def confirm_verification(self, user_id: str) -> bool:
        """Fetch the user's RSI profile and check for the verification code. Returns True if verified."""
        ...

    @abstractmethod
    async def authorize(self, username: str, password: str, redirect_uri: str, state: str) -> AuthCode:
        """Validate credentials and redirect_uri, generate a single-use authorization code."""
        ...

    @abstractmethod
    async def update_user(self, user_id: str, updates: dict) -> User:
        """Update allowed profile fields for a user. Returns the updated user."""
        ...  # pragma: no cover

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> TokenResponse:
        """Exchange a valid authorization code for access + refresh tokens."""
        ...

    @abstractmethod
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> None:
        """Change password for a user after verifying the old password. Revokes all refresh tokens."""
        ...

    @abstractmethod
    async def reset_password(self, user_id: str, new_password: str) -> None:
        """Admin reset of a user's password. Revokes all refresh tokens."""
        ...

    @abstractmethod
    async def forgot_password(self, username: str, rsi_handle: str) -> str:
        """Generate a verification code for password reset via RSI bio. Returns the code."""
        ...

    @abstractmethod
    async def confirm_forgot_password(self, username: str, rsi_handle: str, new_password: str) -> None:
        """Confirm forgot-password by checking RSI bio for verification code, then reset password."""
        ...

    @abstractmethod
    async def introspect_token(self, token: str) -> IntrospectionResult:
        """Validate a JWT access token and return the user's active status plus resolved claims."""
        ...
