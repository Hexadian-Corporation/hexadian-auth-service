class UserNotFoundError(Exception):
    def __init__(self, identifier: str) -> None:
        super().__init__(f"User not found: {identifier}")
        self.identifier = identifier


class UserAlreadyExistsError(Exception):
    def __init__(self, username: str) -> None:
        super().__init__(f"User already exists: {username}")
        self.username = username


class InvalidCredentialsError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid credentials")


class RefreshTokenNotFoundError(Exception):
    def __init__(self, token: str) -> None:
        super().__init__(f"Refresh token not found: {token}")
        self.token = token
