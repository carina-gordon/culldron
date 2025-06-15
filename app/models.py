from datetime import datetime
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    url: str = Field(unique=True)
    content: str
    published_at: datetime
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    theme_id: Optional[int] = Field(default=None, foreign_key="theme.id")
    theme: Optional["Theme"] = Relationship(back_populates="posts")

class Theme(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    thesis: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    posts: List[Post] = Relationship(back_populates="theme")

class ThemeCreate(SQLModel):
    thesis: str

class PostCreate(SQLModel):
    title: str
    url: str
    content: str
    published_at: datetime 