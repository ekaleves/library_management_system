# 📚 Library Management System

A web-based application built with FastAPI to help libraries and educational institutions efficiently manage their book collections, user accounts, and loan transactions.

It provides secure, intuitive access for both users and administrators.

---

## 🚀 Features

- ✅ User registration and JWT-based login
- 📚 Admin-only book creation, editing, and deletion
- 📖 Borrow and return system with due dates and fines
- 🧾 Export loan history as CSV
- 🧠 Smart logic to prevent over-borrowing
- 🧑‍⚖️ Admin route to see overdue loans
- 🧪 Unit tested using Pytest
- 📈 Dashboard-ready endpoints (coming soon!)

---

## 🔧 Tech Stack

| Tool         | Purpose                              |
|--------------|--------------------------------------|
| FastAPI      | Web framework                        |
| SQLAlchemy   | ORM for PostgreSQL                   |
| Pydantic     | Data validation                      |
| Uvicorn      | ASGI Server                          |
| Pytest       | Unit testing                         |
| ReportLab    | (future) PDF generation              |
| JWT (jose)   | Authentication tokens                |
| dotenv       | Environment variable management      |

---

## 📦 API Endpoints

| Endpoint                | Method | Description                                  |
|-------------------------|--------|----------------------------------------------|
| `/register`             | POST   | Register new user                            |
| `/token`                | POST   | Login to receive JWT                         |
| `/books/`               | GET    | View all books                               |
| `/books/`               | POST   | Add new book *(admin only)*                  |
| `/books/{id}`           | PATCH  | Update book *(admin only)*                   |
| `/books/{id}`           | DELETE | Delete book *(admin only)*                   |
| `/loans/`               | POST   | Borrow a book                                |
| `/loans/{id}/return`    | POST   | Return a book                                |
| `/loans/me`             | GET    | View personal loan history                   |
| `/loans/overdue`        | GET    | Admin-only: see overdue loans                |
| `/loans/me/export`      | GET    | Export user's loan history as CSV            |

---

## 🧪 Testing

Run tests with Pytest:

```bash
pytest -v
