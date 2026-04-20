from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenPairResponse
from app.schemas.user import UserResponse
from app.api.service.auth_service import register_user, login_user


router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    return await register_user(data=data, db=db)


@router.post("/login", response_model=TokenPairResponse)
async def login(
        data: LoginRequest,
        db: AsyncSession = Depends(get_db),
                ):
    return await login_user(data=data, db=db)
