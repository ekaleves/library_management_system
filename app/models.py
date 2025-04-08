from sqlalchemy import Column, Numeric, Integer, String, Text, ForeignKey, Float, Date, Boolean
from datetime import datetime
from app.database import Base
from sqlalchemy.orm import relationship


# User model
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    user_email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)

    loans = relationship("Loan", back_populates="user")


# Book model
class Book(Base):
    __tablename__ = "books"

    book_id = Column(Integer, primary_key=True, index=True)
    book_name = Column(String, nullable=False, index=True)
    book_genre = Column(String, nullable=False)
    book_year = Column(Integer, nullable=False)
    book_author = Column(Text, nullable=False)
    book_language = Column(String, nullable=False)
    book_description = Column(Text, nullable=True)
    number_available_volumes = Column(Integer, nullable=False)

    loans = relationship("Loan", back_populates="book")


# Loan model (the association model)
class Loan(Base):
    __tablename__ = "loans"

    loan_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.book_id"), nullable=False)
    loan_due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    loan_fine = Column(Numeric, nullable=True)

    user = relationship("User", back_populates="loans")
    book = relationship("Book", back_populates="loans")
