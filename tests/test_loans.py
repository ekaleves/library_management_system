import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_loans_me_unauthenticated():
    response = client.get("/loans/me")
    assert response.status_code in [401, 403]


def test_get_loans_me_authenticated():
    register_data = {
        "username": "pytestuser",
        "user_email": "pytestuser@example.com",
        "password": "pytestpass"
    }
    register = client.post("/register", json=register_data)
    assert register.status_code in [200, 400]

    login_data = {
        "username": "pytestuser",
        "password": "pytestpass"
    }
    token_response = client.post("/token", data=login_data)
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/loans/me", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_overdue_loans_as_user():
    client.post("/register", json={
        "username": "user_test",
        "user_email": "user_test@example.com",
        "password": "userpass"
    })
    token = client.post("/token", data={
        "username": "user_test",
        "password": "userpass"
    }).json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/loans/overdue", headers=headers)

    assert response.status_code == 403


def test_get_overdue_loans_as_admin():
    from app import database as db, models

    client.post("/register", json={
        "username": "admin_test",
        "user_email": "admin_test@example.com",
        "password": "adminpass"
    })
    token = client.post("/token", data={
        "username": "admin_test",
        "password": "adminpass"
    }).json()["access_token"]

    session = db.SessionLocal()
    admin_user = session.query(models.User).filter_by(username="admin_test").first()
    if admin_user and not admin_user.is_admin:
        admin_user.is_admin = True
        session.commit()
    session.close()

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/loans/overdue", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_borrow_book_success():
    # Register and login borrower
    client.post("/register", json={
        "username": "borrower",
        "user_email": "borrower@example.com",
        "password": "testpass"
    })
    token = client.post("/token", data={
        "username": "borrower",
        "password": "testpass"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get user_id
    user_resp = client.get("/users/borrower", headers=headers)
    user_id = user_resp.json()["user_id"]

    # Register admin and promote
    client.post("/register", json={
        "username": "admin_borrower",
        "user_email": "admin_borrower@example.com",
        "password": "adminpass"
    })
    admin_token = client.post("/token", data={
        "username": "admin_borrower",
        "password": "adminpass"
    }).json()["access_token"]
    from app import database as db, models
    session = db.SessionLocal()
    admin = session.query(models.User).filter_by(username="admin_borrower").first()
    admin.is_admin = True
    session.commit()
    session.close()

    # Create book
    book_data = {
        "book_name": "Unique Pytest Book",
        "book_genre": "Tech",
        "book_year": 2024,
        "book_author": "Test Author",
        "book_language": "English",
        "book_description": "A book for testing",
        "number_available_volumes": 1
    }
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    book_resp = client.post("/books/", json=book_data, headers=admin_headers)
    book_id = book_resp.json()["book_id"]

    # Borrow book
    loan_resp = client.post("/loans/", json={
        "user_id": user_id,
        "book_id": book_id
    }, headers=headers)

    assert loan_resp.status_code == 200
    assert loan_resp.json()["book_id"] == book_id


def test_borrow_book_unavailable():
    # Login and reuse borrower
    token = client.post("/token", data={
        "username": "borrower",
        "password": "testpass"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get user_id
    user_resp = client.get("/users/borrower", headers=headers)
    user_id = user_resp.json()["user_id"]

    # Get book_id
    books = client.get("/books/").json()
    print("Books:", books)
    book_id = next(book["book_id"] for book in books if book["book_name"] == "Unique Pytest Book")

    # Try to borrow again (no copies left)
    response = client.post("/loans/", json={
        "user_id": user_id,
        "book_id": book_id
    }, headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "No available copies to borrow"


def test_export_loans_csv_authenticated():
    # Login again
    token = client.post("/token", data={
        "username": "borrower",
        "password": "testpass"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Call export route
    response = client.get("/loans/me/export", headers=headers)
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment; filename=loan_history.csv" in response.headers["content-disposition"]
    assert "Loan ID" in response.text  # simple CSV check


def test_export_loans_pdf_authenticated():
    token = client.post("/token", data={
        "username": "borrower",
        "password": "testpass"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/loans/me/export/pdf", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == "attachment; filename=loan_history.pdf"
    assert response.content.startswith(b"%PDF")


def test_get_admin_stats():
    # Register and login as admin
    client.post("/register", json={
        "username": "admin_stats",
        "user_email": "admin_stats@example.com",
        "password": "adminpass"
    })
    token = client.post("/token", data={
        "username": "admin_stats",
        "password": "adminpass"
    }).json()["access_token"]

    # Promote to admin in DB
    from app import database as db, models
    session = db.SessionLocal()
    admin = session.query(models.User).filter_by(username="admin_stats").first()
    admin.is_admin = True
    session.commit()
    session.close()

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/admin/stats", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert all(key in data for key in ["total_users", "total_books", "active_loans", "overdue_loans"])
