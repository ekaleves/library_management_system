from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app import schemas, crud, models
from fastapi import HTTPException
from typing import List
from app.database import get_db
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import create_access_token
from app.crud import authenticate_user
from datetime import timedelta
from app.dependencies import get_current_user
from app.models import User
from app.schemas import LoanWithBookUser

router = APIRouter()


@router.post("/books/", response_model=schemas.BookConfig)
def created_book(book: schemas.BookCreate,
                 db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)
                 ):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only Administrator users can create books.")
    return crud.create_book(db, book)


@router.patch("/books/{book_id}", response_model=schemas.BookConfig)
def update_book(
        book_id: int,
        book_data: schemas.BookUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only Administrator users can alter books.")

    return crud.partial_update_book(db, book_id, book_data)


@router.get("/books/", response_model=List[schemas.BookConfig])
def read_all_books(db: Session = Depends(get_db)):
    return crud.get_books(db)


@router.get("/books/{name}", response_model=List[schemas.BookConfig])
def read_book_by_name(name: str, db: Session = Depends(get_db)):
    books = crud.get_book_by_name(db, name)
    if not books:
        raise HTTPException(status_code=404, detail="No books found")
    return books


@router.get("/users/{name}", response_model=schemas.UserConfig)
def get_user(name: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, name)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.post("/register", response_model=schemas.UserConfig)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already taken."
        )
    return crud.create_user(db, user)


@router.post("/token")
def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrent username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=30)

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.delete("/books/{book_id}")
def delete_book(
        book_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only Administrator users can delete books.")
    return crud.delete_book(db, book_id)


@router.post("/loans/", response_model=schemas.LoanConfig)
def borrow_book(
    loan: schemas.LoanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_id != loan.user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can't borrow a book for another user.")
    return crud.create_loan(db, loan)


@router.post("/loans/{loan_id}/return", response_model=schemas.LoanConfig)
def return_book(
    loan_id: int,
    return_data: schemas.LoanReturn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    loan = db.query(models.Loan).filter(models.Loan.loan_id == loan_id).first()

    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found.")

    if loan.user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can't return another user's loan.")

    return crud.return_loan(db, loan_id, return_data)


@router.get("/loans/me", response_model=List[LoanWithBookUser])
def get_my_loans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud.get_loans_by_user(db, current_user.user_id)


@router.get("/loans/overdue", response_model=List[LoanWithBookUser])
def get_overdue_loans(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Administrator users only.")

    return crud.get_overdue_loans(db)


@router.get("/notifications/due-soon", response_model=List[LoanWithBookUser])
def get_due_soon_loans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Administrator users only.")

    return crud.get_loans_due_soon(db)


@router.get("/loans/history", response_model=List[LoanWithBookUser])
def get_loan_history(
    user_id: Optional[int] = None,
    returned: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only.")

    return crud.get_loan_history(db, user_id, returned)













