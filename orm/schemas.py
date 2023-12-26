from typing import Union

from pydantic import BaseModel


class PaperBase(BaseModel):
    title: str
    abstract: Union[str, None] = None
    authors: Union[str, None] = None
    keywords: Union[str, None] = None
    content: Union[str, None] = None
    analysis_result: Union[str, None] = None
    created_at: Union[str, None] = None
    updated_at: Union[str, None] = None


class PaperCreate(PaperBase):
    pass


class Paper(PaperBase):
    id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True