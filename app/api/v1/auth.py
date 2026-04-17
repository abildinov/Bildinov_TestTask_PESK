from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.role import Role
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserResponse
from app.core.security import hash_password


router = APIRouter()


@router.post('/register', response_model= UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
        data: RegisterRequest,
        db: AsyncSession = Depends(get_db),

):
    result = await db.execute(select(User).where(User.email == data.email))
    exiting_user = result.scalar_one_or_none()
    if exiting_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exits",
        )
    default_role_query = db.execute(select(Role).where(Role.name == 'role_1'))
    default_role = db.commit(default_role_query())
    pass


