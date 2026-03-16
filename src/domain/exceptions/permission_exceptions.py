class PermissionNotFoundError(Exception):
    def __init__(self, permission_id: str) -> None:
        super().__init__(f"Permission not found: {permission_id}")
        self.permission_id = permission_id
