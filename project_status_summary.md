# Mobile-Store Management System - Project Documentation

This document serves as a consolidated reference for the setup and configuration of the Mobile-Store system as of September 12, 2026.

---

## 1. Backend (Django + PostgreSQL)
Located in: `backend/`

- **Core Dependencies**: `django`, `djangorestframework`, `djangorestframework-simplejwt`, `psycopg2-binary`, `dj-database-url`, `django-cors-headers`, `cryptography`.
- **Configuration (`backend/mobilestore/settings.py`)**:
    - Configured `DATABASES` using `dj_database_url`.
    - Added `rest_framework`, `corsheaders`, and `api` to `INSTALLED_APPS`.
    - Added `corsheaders.middleware.CorsMiddleware` to `MIDDLEWARE`.
    - Set `AUTH_USER_MODEL = 'api.User'`.
    - Configured `REST_FRAMEWORK` for JWT authentication.
- **Models (`backend/api/models.py`)**:
    - Implemented schemas for: `User` (custom, inheriting AbstractUser), `Customer`, `License`, `Device`, `Token`, `Inventory`, `Sale`, `Repair`.
- **API Endpoints**:
    - Created serializers for `User` and `License` (`backend/api/serializers.py`).
    - Implemented `LicenseCheckView` (`backend/api/views.py`).
    - Configured routing in `backend/api/urls.py` (included in `backend/mobilestore/urls.py`).
- **Status**: Initial migrations generated (`python manage.py makemigrations api`). Database server connection pending.

---

## 2. Desktop Application (PyQt6 + SQLite + AES)
Located in: `desktop/`

- **Environment**: Python virtualenv.
- **Dependencies**: `PyQt6`, `requests`, `cryptography`.
- **Encryption**: Used `cryptography.fernet` for local token encryption.
- **Local Storage**: `local_storage.db` (SQLite) with table `tokens`.
- **GUI (`desktop/main.py`)**: PyQt6 window providing a "Verify License" interface.
- **Integration**: Foundation implemented for API license verification (placeholder in `verify_license`).

---

## 3. Frontend (React + Vite)
Located in: `frontend/`

- **Core Dependencies**: `react`, `react-dom`, `react-router-dom`, `axios`.
- **Setup**: Initialized as a TypeScript project.
- **API Integration (`frontend/src/api.ts`)**: Configured `axios` instance with `baseURL: 'http://localhost:8000/api'` and request interceptor for JWT `Authorization` header.
- **Routing (`frontend/src/App.tsx`)**: Implemented routing for `/login`, `/dashboard`, `/inventory`, `/sales`, `/repairs`.
- **Components**:
    - Created placeholder components: `InventoryList.tsx`, `CustomerManagement.tsx`.
- **Execution**: Project configured to run via Vite (expected command: `npm run dev`) at `http://localhost:5173`.

---
*Note: The mobile/ directory remains uninitialized due to missing Flutter SDK in the current environment.*
