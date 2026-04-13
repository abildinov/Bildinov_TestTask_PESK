from pydantic import BaseModel


class ContentResponse(BaseModel):
    id: int
    title: str
    body: str
    access_level: str
