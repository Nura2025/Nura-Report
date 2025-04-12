from typing import Union
from fastapi import Depends, HTTPException ,status
from app.api.dependinces import get_current_user
from app.db.models import Clinician, Patient, UserRole


class RoleChecker:
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Union[Patient, Clinician] = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return user