from uuid import uuid4
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
import jwt
from pydantic import SecretStr

from app.core.config import get_settings

settings = get_settings()


password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")


def hash_password(password: SecretStr) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_token(payload: dict, expires_delta: timedelta) -> str:
    to_encode = payload.copy()

    now: datetime = datetime.now(timezone.utc)
    expires: datetime = now + expires_delta

    to_encode['iat'] = now # время выпуска
    to_encode['exp'] = expires # срок жизни

    token: str = jwt.encode(to_encode,
                       settings.jwt_secret_key.get_secret_value(),
                       algorithm=settings.jwt_algorithm,
                       )

    return token


def create_access_token(user_id: int, session_id: str, roles: list[str]) -> str:
    payload = {
        "sub": str(user_id),
        "jti": str(uuid4()),
        "sid": session_id,
        "type": "access",
        "roles": roles,
    }
    return create_token(payload, timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(user_id: int, session_id: str) -> str:
    payload = {
        "sub": str(user_id),
        "jti": str(uuid4()),
        "sid": session_id,
        "type": "refresh",
    }
    return create_token(payload, timedelta(days=settings.refresh_token_expire_days))


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )



