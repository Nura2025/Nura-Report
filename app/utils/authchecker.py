from fastapi import Depends, HTTPException ,status
from app.api.dependinces import get_auth_role
from app.db.models import UserRole


class AuthChecker:
    def __init__(self, *roles: UserRole):
        self.roles = roles

    def __call__(self, user_role: UserRole = Depends(get_auth_role)):
        if user_role not in self.roles:
            roles_values = " or ".join([role.value for role in self.roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {roles_values}"
            )
