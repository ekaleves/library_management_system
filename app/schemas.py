from pydantic import BaseModel
from datetime import date
from typing import Optional
from decimal import Decimal


class UserBase(BaseModel):
    username: str
    user_email: str


class UserCreate(UserBase):
    password: str


class UserConfig(UserBase):
    user_id: int
    is_admin: bool

    model_config = {
        "from_attributes": True
    }


class BookBase(BaseModel):
    book_name: str
    book_genre: str
    book_year: int
    book_author: str
    book_language: str
    book_description: Optional[str] = None
    number_available_volumes: int


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    book_name: Optional[str] = None
    book_genre: Optional[str] = None
    book_year: Optional[int] = None
    book_author: Optional[str] = None
    book_language: Optional[str] = None
    book_description: Optional[str] = None
    number_available_volumes: Optional[int] = None


class BookConfig(BookBase):
    book_id: int

    model_config = {
        "from_attributes": True
    }


class LoanBase(BaseModel):
    user_id: int
    book_id: int
    loan_due_date: date
    return_date: Optional[date] = None
    loan_fine: Optional[Decimal] = None


class LoanCreate(LoanBase):
    loan_due_date: Optional[date] = None


class LoanReturn(BaseModel):
    return_date: Optional[date] = None


class LoanConfig(LoanBase):
    loan_id: int

    model_config = {
        "from_attributes": True
    }


class LoanWithBookUser(LoanConfig):
    user: UserConfig
    book: BookConfig























