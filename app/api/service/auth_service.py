from uuid import uuid4

from redis.asyncio import Redis
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.role import Role
from app.models.user_sessions import UserSession
from app.schemas.auth import RegisterRequest, LoginRequest, TokenPairResponse, RefreshRequest
from app.schemas.user import UserResponse
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from fastapi import HTTPException, status
from app.db.redis import settings




async def register_user(data: RegisterRequest, db: AsyncSession) -> UserResponse:
    stmt = await db.execute(select(User).where(User.email == data.email))
    result = stmt.scalar_one_or_none()
    if result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с такой почтой уже существует"
        )
    role_result = await db.execute(select(Role).where(Role.name == 'role_1'))
    default_role = role_result.scalar_one_or_none()
    if default_role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    hashed_password = hash_password(data.password)
    new_user = User(
        email=data.email,
        hashed_password=hashed_password
    )
    new_user.roles.append(default_role)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        is_active=new_user.is_active,
        roles=[default_role.name],
    )


async def login_user(data: LoginRequest,
                     db: AsyncSession,
                     redis_client: Redis) -> TokenPairResponse:
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.email == data.email)
    )
    res_login = result.scalar_one_or_none()
    if not res_login or not verify_password(
            data.password.get_secret_value(),
            res_login.hashed_password
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Неверный пароль или почта'
                            )
    if res_login.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь заблокирован",
        )

    roles = [role.name for role in res_login.roles]
    session_id = str(uuid4())

    new_session = UserSession(user_id=res_login.id,
                              session_id=session_id,
                              )
    db.add(new_session)

    access_token = create_access_token(
        user_id=res_login.id,
        session_id=session_id,
        roles=roles
    )
    refresh_token = create_refresh_token(
        user_id=res_login.id,
        session_id=session_id
    )
    access_payload  = decode_token(access_token)
    refresh_payload  = decode_token(refresh_token)
    access_jti = access_payload['jti']
    refresh_jti = refresh_payload['jti']
    await redis_client.set(
        f'whitelist:access:{access_jti}',
        "1",
        ex=settings.access_token_expire_minutes * 60
    )
    await redis_client.set(
        f'whitelist:refresh:{refresh_jti}',
        "1",
        ex=settings.refresh_token_expire_days * 24 * 60 * 60
    )
    await redis_client.sadd(
        f'session_tokens:{session_id}',
        "1",
        access_jti, refresh_jti
    )

    await db.commit()
    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


async def refresh_tokens(
        data: RefreshRequest,
        db: AsyncSession,
        redis_client: Redis,
) -> TokenPairResponse:
    refresh_token = data.refresh_token
    payload = decode_token(refresh_token)
    if payload['type'] != 'refresh':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    refresh_jti = payload['jti']
    session_id = payload['sid']
    user_id = int(payload["sub"])
    whitelist_value = await redis_client.get(f'whitelist:refresh:{refresh_jti}')
    blacklist_value = await redis_client.get(f'blacklist:{refresh_jti}')
    if whitelist_value is None or blacklist_value is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked token"
        )
    db_res = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id)
    )
    user = db_res.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    roles = [role.name for role in user.roles]

    new_access_token = create_access_token(
        user_id=user.id,
        session_id=session_id,
        roles=roles,
    )

    new_refresh_token = create_refresh_token(
        user_id=user.id,
        session_id=session_id,
    )

    new_access_payload = decode_token(new_access_token)
    new_refresh_payload = decode_token(new_refresh_token)

    new_access_jti = new_access_payload["jti"]
    new_refresh_jti = new_refresh_payload["jti"]

    await redis_client.delete(f"whitelist:refresh:{refresh_jti}")

    await redis_client.set(
        f"blacklist:{refresh_jti}",
        "1",
        ex=settings.refresh_token_expire_days * 24 * 60 * 60,
    )

    await redis_client.set(
        f"whitelist:access:{new_access_jti}",
        "1",
        ex=settings.access_token_expire_minutes * 60,
    )

    await redis_client.set(
        f"whitelist:refresh:{new_refresh_jti}",
        "1",
        ex=settings.refresh_token_expire_days * 24 * 60 * 60,
    )

    await redis_client.sadd(
        f"session_tokens:{session_id}",
        new_access_jti,
        new_refresh_jti,
    )

    return TokenPairResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


async def logout_user(
    token: str,
    db: AsyncSession,
    redis_client: Redis,
):
    payload = decode_token(token)

    if payload["type"] != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    session_id = payload["sid"]
    session_jtis = await redis_client.smembers(f"session_tokens:{session_id}")

    for session_jti in session_jtis:
        await redis_client.delete(f"whitelist:access:{session_jti}")
        await redis_client.delete(f"whitelist:refresh:{session_jti}")
        await redis_client.set(
            f"blacklist:{session_jti}",
            "1",
            ex=settings.refresh_token_expire_days * 24 * 60 * 60,
        )

    smnt = await db.execute(
        select(UserSession).where(UserSession.session_id == session_id)
    )
    session_obj = smnt.scalar_one_or_none()

    if session_obj is not None:
        session_obj.is_revoked = True
        await db.commit()

    return {"message": "Logged out"}

# наверное здесь должна быть функция logout
# blacklist:{jti}
