from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models, schemas
from app.models import User
from app.security import hash_password, verify_password
from datetime import datetime, timedelta, date
from fastapi import HTTPException
from decimal import Decimal
from typing import Optional
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import csv
import io


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
        loan.loan_fine = Decimal(days_late) * Decimal("1.50")

    # Update book inventory
    book = db.query(models.Book).filter(models.Book.book_id == loan.book_id).first()
    if book:
        book.number_available_volumes += 1

    db.commit()
    db.refresh(loan)
    return loan


def get_loans_by_user(db: Session, user_id: int):
    return (
        db.query(models.Loan)
        .filter(models.Loan.user_id == user_id)
        .order_by(models.Loan.loan_due_date.desc())
        .all()
    )


def get_overdue_loans(db: Session):
    return (
        db.query(models.Loan)
        .filter(
            models.Loan.return_date.is_(None),  # not returned
            models.Loan.loan_due_date < date.today()  # past due
        )
        .order_by(models.Loan.loan_due_date.asc())
        .all()
    )


def get_loans_due_soon(db: Session, days_ahead: int = 3):
    from datetime import date, timedelta

    today = date.today()
    upcoming = today + timedelta(days=days_ahead)

    return (
        db.query(models.Loan)
        .filter(
            models.Loan.return_date.is_(None),
            models.Loan.loan_due_date <= upcoming,
            models.Loan.loan_due_date >= today
        )
        .order_by(models.Loan.loan_due_date.asc())
        .all()
    )


def get_loan_history(
    db: Session,
    user_id: Optional[int] = None,
    returned: Optional[bool] = None
):
    query = db.query(models.Loan)

    if user_id is not None:
        query = query.filter(models.Loan.user_id == user_id)

    if returned is not None:
        if returned:
            query = query.filter(models.Loan.return_date.isnot(None))
        else:
            query = query.filter(models.Loan.return_date.is_(None))

    return query.order_by(models.Loan.loan_due_date.desc()).all()


def generate_user_loans_csv(db: Session, user_id: int) -> str:
    loans = (
        db.query(models.Loan)
        .filter(models.Loan.user_id == user_id)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Loan ID", "Book Title", "Due Date", "Return Date", "Fine"])

    # Rows
    for loan in loans:
        writer.writerow([
            loan.loan_id,
            loan.book.book_name,
            loan.loan_due_date,
            loan.return_date or "",
            str(loan.loan_fine or "0.00")
        ])

    return output.getvalue()


def generate_user_loans_pdf(db: Session, user_id: int) -> bytes:
    loans = (
        db.query(models.Loan)
        .filter(models.Loan.user_id == user_id)
        .all()
    )

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 40
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, y, "Loan History")
    y -= 30

    pdf.setFont("Helvetica", 10)
    for loan in loans:
        book_name = loan.book.book_name
        due = str(loan.loan_due_date)
        returned = str(loan.return_date) if loan.return_date else "-"
        fine = str(loan.loan_fine or "0.00")
        line = f"{loan.loan_id}: {book_name} | Due: {due} | Returned: {returned} | Fine: ${fine}"
        pdf.drawString(40, y, line)
        y -= 18
        if y < 50:
            pdf.showPage()
            y = height - 40
            pdf.setFont("Helvetica", 10)

    pdf.save()
    buffer.seek(0)
    return buffer.read()


def get_admin_dashboard_stats(db: Session):
    total_users = db.query(func.count(models.User.user_id)).scalar()
    total_books = db.query(func.count(models.Book.book_id)).scalar()
    active_loans = db.query(func.count(models.Loan.loan_id)).filter(models.Loan.return_date == None).scalar()
    overdue_loans = db.query(func.count(models.Loan.loan_id)).filter(
        models.Loan.return_date == None,
        models.Loan.loan_due_date < date.today()
    ).scalar()

    return {
        "total_users": total_users,
        "total_books": total_books,
        "active_loans": active_loans,
        "overdue_loans": overdue_loans
    }


