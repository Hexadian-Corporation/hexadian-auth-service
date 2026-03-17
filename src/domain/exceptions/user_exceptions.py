class UserNotFoundError(Exception):
    def __init__(self, identifier: str) -> None:
        super().__init__(f"User not found: {identifier}")
        self.identifier = identifier


class UserAlreadyExistsError(Exception):
    def __init__(self, identifier: str, field: str = "username") -> None:
        super().__init__(f"User already exists: {identifier}")
        self.identifier = identifier
        self.field = field


class InvalidCredentialsError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid credentials")


class RefreshTokenNotFoundError(Exception):
    def __init__(self, token: str) -> None:
        super().__init__(f"Refresh token not found: {token}")
        self.token = token


class InvalidAuthCodeError(Exception):
    def __init__(self, reason: str = "Invalid or expired authorization code") -> None:
        super().__init__(reason)


class InvalidRedirectUriError(Exception):
    def __init__(self, redirect_uri: str) -> None:
        super().__init__(f"Invalid redirect URI: {redirect_uri}")
        self.redirect_uri = redirect_uri


class InvalidPasswordError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class RsiHandleMismatchError(Exception):
    def __init__(self, username: str) -> None:
        super().__init__(f"RSI handle does not match user: {username}")
        self.username = username
