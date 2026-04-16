from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.user import User
from app.models.role import Role
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserResponse
from app.core.security import hash_password





