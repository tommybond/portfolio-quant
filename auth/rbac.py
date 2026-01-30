"""Role-based access control."""

ROLE_LEVEL = {"admin": 3, "user": 2, "guest": 1}


def check_permission(user_role: str, resource: str, action: str) -> bool:
    level = ROLE_LEVEL.get(user_role, 0)
    if level >= ROLE_LEVEL["admin"]:
        return True
    if resource in ("trades", "positions", "risk") and action in ("read", "create", "update"):
        return level >= ROLE_LEVEL["user"]
    return level >= ROLE_LEVEL["guest"]


class RBAC:
    def __init__(self, user_role: str = "guest"):
        self.user_role = user_role

    def can(self, resource: str, action: str) -> bool:
        return check_permission(self.user_role, resource, action)
