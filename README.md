# Library API

REST API for a community library: staff manage the book catalogue, visitors borrow and return books. Registration is email-verified, authentication is JWT, lifecycle emails and daily overdue reminders run through Celery.

**Stack:** Django 5.2 · Django REST Framework 3.16 · PostgreSQL 16 · Celery 5.5 + Redis · Docker Compose · simplejwt

## Roles

- **Library user (staff)** — created via `createsuperuser` or the admin panel. Manages books, deletes users, views visitors' loans.
- **Visitor** — self-registers through the API, must activate the account via the emailed link, then can borrow/return books and view own loans.

## Run

1. Create the env file (dev defaults work out of the box):

   ```
   cp app/.env.example app/.env
   ```

2. Build and start the stack (`app` :8321, `db` :5321, `flower` :5555, plus `redis`, `worker`, `beat`):

   ```
   docker compose up --build
   ```

3. Create a staff account:

   ```
   docker compose run --rm app sh -c "python manage.py createsuperuser"
   ```

Emails use the console backend by default — activation and notification emails appear in the `worker` service logs. The daily overdue-reminder job runs via Celery beat at 00:00 UTC (`send-overdue-notifications-daily`).

## Tests & lint

```
docker compose run --rm app sh -c "python manage.py wait_for_db && python manage.py test"
docker compose run --rm app sh -c "flake8 && isort --check-only ."
```

## API

Authenticated endpoints expect the header `Authorization: Bearer <access>`.

### Auth & users

| Method | URL | Access | Description |
|---|---|---|---|
| POST | `/api/users/` | public | Register a visitor: `{"name", "email", "password"}` → 201. The account starts inactive; an activation link is emailed. |
| GET | `/api/activate/<token>/` | public | Activation link from the email (token expires in 3 days). |
| POST | `/api/login/` | public | `{"email", "password"}` → `{"access", "refresh", "id", "user_type"}`. Access token lives 60 minutes. |
| POST | `/api/logout/` | authenticated | `{"refresh"}` — blacklists the refresh token. |
| DELETE | `/api/users/<id>/` | staff | Staff delete themselves or a visitor. Blocked while the target has active loans; staff cannot delete other staff. |

### Books

| Method | URL | Access | Description |
|---|---|---|---|
| GET | `/api/books/` | authenticated | List all books. |
| POST | `/api/books/` | staff | `{"title", "author", "total_copies"}` — `available_copies` starts equal to `total_copies`. |
| GET | `/api/books/<id>/` | authenticated | Book detail. |
| PATCH | `/api/books/<id>/` | staff | Partial update. Shrinking `total_copies` below `available_copies` clamps it to `available_copies`; growing it raises `available_copies` by the same delta. |
| DELETE | `/api/books/<id>/` | staff | Only when all copies are returned (`available_copies == total_copies`). |

### Loans

| Method | URL | Access | Description |
|---|---|---|---|
| POST | `/api/loans/` | visitor | `{"book": <id>}` — borrow a copy, due in 30 days. One active loan per book per member. Emails the borrower and the staff. |
| POST | `/api/loans/<id>/returned/` | visitor | Return the loan. Emails the borrower and the staff. |
| GET | `/api/loans/` | authenticated | Visitor: own active loans. Staff: requires `?member=<id>`, lists that visitor's active loans. |

### Admin

`http://localhost:8321/admin/` — Django admin for users, books and loans.

Errors are returned as `{"code": "<MACHINE_READABLE_CODE>", "detail": ...}`.
