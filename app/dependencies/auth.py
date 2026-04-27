from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.security import decode_token
from app.db.redis import get_redis

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(access_token: str = Depends(oauth2_scheme),
                           db: AsyncSession = Depends(get_db),
                           redis_client: Redis = Depends(get_redis),
                           ) -> User:
    payload =decode_token(access_token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    access_jti = payload['jti']
    whitelist_value = await redis_client.get(f"whitelist:access:{access_jti}")
    blacklist_value = await redis_client.get(f"blacklist:{access_jti}")
    if whitelist_value is None or blacklist_value is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked token"
        )
    user_id = int(payload.get("sub"))
    db_res = await db.execute(select(User).where(User.id == user_id))
    current_user = db_res.scalar_one_or_none()
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return current_user

