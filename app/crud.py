from sqlalchemy.orm import Session
from app import models, schemas
from app.models import User
from app.security import hash_password, verify_password
from datetime import datetime, timedelta, date
from fastapi import HTTPException
from decimal import Decimal


def create_book(db: Session, book_data: schemas.BookCreate):
    new_book = models.Book(**book_data.dict())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


def get_books(db: Session):
    return db.query(models.Book).all()


def get_book_by_name(db: Session, book_name: str):
    return db.query(models.Book).filter(models.Book.book_name.ilike(f"%{book_name}%")).all()


def partial_update_book(
        db: Session,
        book_id: int,
        book_data: schemas.BookUpdate,
):
    book = db.query(models.Book).filter(models.Book.book_id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found.")

    for key, value in book_data.dict(exclude_unset=True).items():
        setattr(book, key, value)

    db.commit()
    db.refresh(book)

    return book


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user_data: schemas.UserCreate):
    hashed_pw = hash_password(user_data.password)
    new_user = models.User(
        username=user_data.username,
        user_email=user_data.user_email,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def delete_book(db: Session, book_id: int):
    book = db.query(models.Book).filter(models.Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    db.delete(book)
    db.commit()
    return {"message": "Book deleted successfully"}


def create_loan(db: Session, loan_data: schemas.LoanCreate):
    # Get the book
    book = db.query(models.Book).filter(models.Book.book_id == loan_data.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check availability
    if book.number_available_volumes <= 0:
        raise HTTPException(status_code=400, detail="No available copies to borrow")

    # Set default due date if not provided
    due_date = loan_data.loan_due_date or (datetime.utcnow().date() + timedelta(days=14))

    # Create the loan
    loan = models.Loan(
        user_id=loan_data.user_id,
        book_id=loan_data.book_id,
        loan_due_date=due_date
    )

    # Update inventory
    book.number_available_volumes -= 1

    db.add(loan)
    db.commit()
    db.refresh(loan)

    return loan


def return_loan(db: Session, loan_id: int, return_data: schemas.LoanReturn):
    loan = db.query(models.Loan).filter(models.Loan.loan_id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    if loan.return_date:
        raise HTTPException(status_code=400, detail="Book already returned")

    return_date = return_data.return_date or date.today()
    loan.return_date = return_date

    # Late return?
    if return_date > loan.loan_due_date:
        days_late = (return_date - loan.loan_due_date).days
        loan.loan_fine = Decimal(days_late) * Decimal("1.50")  # example: $1.50 per day

    # Update book inventory
    book = db.query(models.Book).filter(models.Book.book_id == loan.book_id).first()
    if book:
        book.number_available_volumes += 1

    db.commit()
    db.refresh(loan)
    return loan





