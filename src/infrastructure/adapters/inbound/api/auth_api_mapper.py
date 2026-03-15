from src.domain.models.user import User
from src.infrastructure.adapters.inbound.api.auth_dto import UserDTO


class AuthApiMapper:
    @staticmethod
    def to_dto(user: User) -> UserDTO:
        return UserDTO(
            _id=user.id,
            username=user.username,
            email=user.email,
            roles=user.roles,
            is_active=user.is_active,
            rsi_handle=user.rsi_handle,
            rsi_verified=user.rsi_verified,
        )
