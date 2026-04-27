from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import get_redis
from app.dependencies.auth import get_current_user, oauth2_scheme
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenPairResponse, RefreshRequest
from app.schemas.user import UserResponse
from app.api.service.auth_service import register_user, login_user, refresh_tokens, logout_user

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
        redis_client: Redis = Depends(get_redis),
                ):
    return await login_user(data=data, db=db, redis_client=redis_client)

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    roles = [rol.name for rol in current_user.roles]
    return UserResponse(id=current_user.id, email=current_user.email, is_active=current_user.is_active, roles=roles)

@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
):
    return await refresh_tokens(data=data, db=db, redis_client=redis_client)

@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
):
    return await logout_user(token=token, db=db, redis_client=redis_client)