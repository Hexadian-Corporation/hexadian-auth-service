class GroupNotFoundError(Exception):
    def __init__(self, group_id: str) -> None:
        super().__init__(f"Group not found: {group_id}")
        self.group_id = group_id
