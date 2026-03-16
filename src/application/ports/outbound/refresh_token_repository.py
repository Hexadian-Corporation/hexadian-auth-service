from abc import ABC, abstractmethod

from src.domain.models.refresh_token import RefreshToken


class RefreshTokenRepository(ABC):
    @abstractmethod
    def save(self, token: RefreshToken) -> RefreshToken: ...

    @abstractmethod
    def find_by_token(self, token: str) -> RefreshToken | None: ...

    @abstractmethod
    def revoke(self, token: str) -> None: ...

    @abstractmethod
    def revoke_all_for_user(self, user_id: str) -> None: ...
