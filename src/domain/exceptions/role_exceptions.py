class RoleNotFoundError(Exception):
    def __init__(self, role_id: str) -> None:
        super().__init__(f"Role not found: {role_id}")
        self.role_id = role_id
