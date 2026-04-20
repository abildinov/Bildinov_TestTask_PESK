from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.role import Role
from app.models.user_sessions import UserSession
from app.schemas.auth import RegisterRequest, LoginRequest, TokenPairResponse
from app.schemas.user import UserResponse
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from fastapi import HTTPException, status


async def register_user(data: RegisterRequest, db: AsyncSession) -> UserResponse:
    stmt = await db.execute(select(User).where(User.email == data.email))
    result = stmt.scalar_one_or_none()
    if result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Пользователь с такой почтой уже существует")
    role_result = await db.execute(select(Role).where(Role.name == 'role_1'))
    default_role = role_result.scalar_one_or_none()
    if default_role is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            )
    hashed_password = hash_password(data.password)
    new_user = User(email=data.email,
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
        roles=[role.name for role in new_user.roles],
    )


async def login_user(data: LoginRequest,
                     db: AsyncSession) -> TokenPairResponse:
    result = await db.execute(select(User).where(User.email == data.email))
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

    token = create_access_token(user_id=res_login.id, session_id=session_id, roles=roles)
    refresh_token = create_refresh_token(user_id=res_login.id, session_id=session_id)
    await db.commit()
    return TokenPairResponse(access_token=token,
                             refresh_token=refresh_token,
                             token_type="bearer"

                             )
