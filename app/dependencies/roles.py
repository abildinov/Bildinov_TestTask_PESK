from fastapi import Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.models.user import User


def require_roles(*allowed_roles) :
    async def checker(current_user: User = Depends(get_current_user)):
        matched_roles = [role.name for role in current_user.roles if role.name in allowed_roles]
        if  not matched_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect role")

        return current_user
    return checker



