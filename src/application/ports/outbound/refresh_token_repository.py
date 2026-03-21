from abc import ABC, abstractmethod

from src.domain.models.refresh_token import RefreshToken


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def save(self, token: RefreshToken) -> RefreshToken: ...

    @abstractmethod
    async def find_by_token(self, token: str) -> RefreshToken | None: ...

    @abstractmethod
    async def revoke(self, token: str) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: str) -> None: ...
