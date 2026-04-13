from pydantic import BaseModel, EmailStr, Field


class ContentResponse(BaseModel):
    id: int
    title: str
    body: str
    access_level: str
