from pydantic import BaseModel
from typing import Optional  

# ---------- Books Schemas ----------
class BookBase(BaseModel):
    title: str
    author: str
    year: int
    editorial: str
    pages: int

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None 
    author: Optional[str] = None
    year: Optional[int] = None
    editorial: Optional[str] = None
    pages: Optional[int] = None

class BookResponse(BookBase):
    id: int

    class Config:
        orm_mode = True 

# ---------- User Schemas ----------

class UserLogin(BaseModel):
    username: str
    password: str

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str  

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True 
