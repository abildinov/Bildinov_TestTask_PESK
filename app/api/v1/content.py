from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.dependencies.roles import require_roles
from app.models.content import ContentItem
from app.models.user import User
from app.schemas.content import ContentResponse




router = APIRouter()

@router.get("/common", response_model=list[ContentResponse])
async def get_common_content(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("role_1", "role_2")),
):
    smnt = await db.execute(
        select(ContentItem).where(ContentItem.access_level == "common")
    )
    result_content = smnt.scalars().all()
    return result_content


@router.get("/role-1", response_model=list[ContentResponse])
async def get_role_1_content(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("role_1")),
):
    smnt = await db.execute(
        select(ContentItem).where(ContentItem.access_level == "role_1")
    )
    result_content = smnt.scalars().all()
    return result_content


@router.get("/role-2", response_model=list[ContentResponse])
async def get_role_2_content(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("role_2")),
):
    smnt = await db.execute(
        select(ContentItem).where(ContentItem.access_level == "role_2")
    )
    result_content = smnt.scalars().all()
    return result_content
