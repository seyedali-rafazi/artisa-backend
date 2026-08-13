# ⚡ Artisa Backend API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=flat-square&logo=mongodb)](https://www.mongodb.com/)
[![Beanie](https://img.shields.io/badge/Beanie_ODM-1.24-black?style=flat-square)](https://beanie-odm.dev/)
[![Pytest](https://img.shields.io/badge/Pytest-Passing-0A9EDC?style=flat-square&logo=pytest)](https://docs.pytest.org/)

Production-ready RESTful API backend for **Artisa (آرتیسا)** — Iranian online art gallery and luxury handcraft e-commerce platform. Built with **FastAPI**, **MongoDB** (Beanie ODM async driver), **JWT Authentication**, and deployable to **Vercel** or traditional cloud hosts.

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [📂 Directory Structure](#-directory-structure)
- [🚀 Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Database Setup & Seeding](#database-setup--seeding)
  - [Running the Server](#running-the-server)
- [🧪 Running Tests](#-running-tests)
- [📡 API Documentation & Endpoints](#-api-documentation--endpoints)
- [🌐 Deployment](#-deployment)

---

## ✨ Features

- **🛍️ Product Catalog & Search**:
  - Full-text product search, category filtering, price bounds, special offers (`isSpecial`), and best sellers (`isBestSeller`).
  - Multi-field sorting (price, date, popularity) and dynamic pagination.
- **💬 Reviews & Comment System**:
  - Customer review submission with star ratings.
  - Moderation workflow: admin review approval/rejection before public listing.
- **🔐 User Authentication & Authorization**:
  - Dual JWT token system (Access + Refresh tokens with HTTP-only cookies or bearer tokens).
  - Secure password hashing using `bcrypt` via `passlib`.
  - Google OAuth 2.0 single sign-on (SSO) login.
  - Password recovery flow and email verification integration (Resend API).
  - Role-based access control (User, Admin, Super Admin).
- **📦 Order & Checkout Management**:
  - Checkout order creation with address association and order calculation.
  - User order history and status tracking.
  - Public order tracking using unique tracking codes.
  - Admin status updates (Pending, Processing, Shipped, Delivered, Cancelled).
- **📍 Saved Address Book**:
  - Full address CRUD and default shipping address toggling.
- **💖 Wishlist & Favorites**:
  - Toggle and manage personal favorite products.
- **📰 Content Management**:
  - Hero slider banners API for home page.
  - Blog articles and FAQ management APIs.
- **📁 Media & Blob Storage**:
  - Image upload handler with Vercel Blob storage integration and static file fallback.
- **📐 Standard Response Envelope**:
  - Unified JSON response format across all endpoints: `{ "success": boolean, "message": string, "data": object | array | null }`.

---

## 🛠️ Tech Stack

| Component | Technology | Description |
|---|---|---|
| **Framework** | [FastAPI 0.109](https://fastapi.tiangolo.com/) | High-performance Python web framework |
| **Server** | [Uvicorn 0.27](https://www.uvicorn.org/) | Lightning-fast ASGI server |
| **Database** | [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) | Cloud NoSQL Document Database |
| **Async Driver & ODM** | [Motor 3.3](https://motor.readthedocs.io/) + [Beanie 1.24](https://beanie-odm.dev/) | Async MongoDB ODM built on Pydantic |
| **Data Validation** | [Pydantic v2](https://docs.pydantic.dev/) | Strict data parsing and validation |
| **Auth & Security** | `python-jose` + `passlib` (bcrypt) | JWT generation, token verification & password hashing |
| **Configuration** | `python-decouple` | Environment variable management |
| **Storage & Email** | Vercel Blob + Resend API | Product media hosting and email delivery |
| **Testing** | [Pytest](https://docs.pytest.org/) + `httpx` | Async endpoint & unit testing suite |

---

## 📂 Directory Structure

```
backend/
├── api/
│   └── v1/                          # API Version 1 Routers
│       ├── __init__.py              # V1 router aggregation
│       ├── addresses.py             # User saved addresses
│       ├── admin.py                 # Admin dashboard & system metrics
│       ├── auth.py                  # Auth: Register, Login, Refresh, Password Reset, OAuth
│       ├── banners.py               # Home hero banners configuration
│       ├── blog.py                  # Blog articles & news
│       ├── comments.py              # Product reviews & ratings
│       ├── faqs.py                  # Frequently asked questions
│       ├── favorites.py             # User favorites / saved items
│       ├── orders.py                # Order placement, tracking & history
│       ├── products.py              # Product catalog search, filter & management
│       ├── uploads.py               # Media upload handler (Vercel Blob / Local)
│       ├── users.py                 # Profile edit & account security
│       └── wishlist.py              # Wishlist management
├── core/
│   ├── config.py                    # Application settings (python-decouple)
│   ├── database.py                  # Motor client & Beanie ODM initialization
│   └── security.py                  # Password hashing, JWT encoding/decoding
├── models/                          # Beanie ODM Document Schemas
│   ├── address.py                   # Address collection document
│   ├── banner.py                    # Hero banner document
│   ├── blog.py                      # Blog article document
│   ├── comment.py                   # Comment document
│   ├── faq.py                       # FAQ document
│   ├── order.py                     # Order document
│   ├── product.py                   # Product document
│   ├── user.py                      # User document
│   └── wishlist.py                  # Wishlist document
├── schemas/                         # Pydantic DTO Request/Response Schemas
│   ├── address.py
│   ├── admin.py
│   ├── auth.py
│   ├── comment.py
│   ├── order.py
│   ├── product.py
│   └── user.py
├── tests/                           # Automated Pytest Suite
│   ├── conftest.py                  # Test database fixtures & async client
│   ├── test_blob_storage.py         # Blob storage unit tests
│   ├── test_comments.py             # Comments integration tests
│   ├── test_comments_unit.py        # Comments unit tests
│   ├── test_favorites.py            # Favorites integration tests
│   ├── test_favorites_unit.py       # Favorites unit tests
│   └── test_image_processing.py     # Image processing helper tests
├── .env.example                     # Environment configuration blueprint
├── API_DOCUMENTATION.md             # Detailed endpoint reference markdown
├── Artisa.postman_collection.json   # Postman collection for API testing
├── bruno/                           # Bruno collection configuration
├── main.py                          # Application entry point & FastAPI setup
├── pytest.ini                       # Pytest configuration settings
├── requirements.txt                 # Python package dependencies
├── seed_data.py                     # Mock catalog data seeder script
├── seed_super_admin.py              # Initial Super Admin creation script
└── vercel.json                      # Vercel serverless deployment config
```

---

## 🚀 Getting Started

### Prerequisites

- **Python**: `3.10` or higher (`3.12` recommended)
- **MongoDB**: A running local MongoDB server or a [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) cluster.

### Installation

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   - **Windows**:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

Copy `.env.example` to `.env` in the `backend/` root directory:

```bash
cp .env.example .env
```

Update the values inside `.env`:

```env
# Application Settings
DEBUG=True

# Security Secret Key (Generate via: openssl rand -hex 32)
SECRET_KEY=your-super-secret-key-min-32-chars

# JWT Token Expiration (minutes)
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# MongoDB Configuration (Password in URI MUST be URL-encoded!)
MONGODB_URI=mongodb+srv://username:ENCODED_PASSWORD@cluster0.mongodb.net/
MONGODB_NAME=artisa_db

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Auth Cookies
COOKIE_SECURE=False
COOKIE_SAMESITE=lax

# Google OAuth Credentials (Optional for local dev)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Resend Email Configuration (Optional)
RESEND_API_KEY=re_your_resend_api_key
EMAIL_FROM=noreply@artisa.com

# Vercel Blob Image Storage (Optional)
BLOB_STORE_ID=your_blob_store_id
BLOB_READ_WRITE_TOKEN=your_blob_token
```

> ⚠️ **Note on MongoDB Passwords**: Special characters in your database password (e.g. `@`, `%`, `+`, `*`) must be URL-encoded in the connection URI. Python helper:
> ```python
> from urllib.parse import quote_plus
> print(quote_plus("your-password"))
> ```

### Database Setup & Seeding

1. **Seed Initial Products & Categories**:
   ```bash
   python seed_data.py
   ```
   *Seeds sample categories, products, banners, blog posts, and FAQs into MongoDB.*

2. **Seed Super Admin Account**:
   ```bash
   python seed_super_admin.py
   ```
   *Creates the initial system admin user for accessing `/api/v1/admin` endpoints.*

### Running the Server

Start the ASGI development server with live reload:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

---

## 🧪 Running Tests

The backend uses **Pytest** with async support (`pytest-asyncio`).

Run the test suite:

```bash
# Run all tests
pytest

# Run tests with detailed output
pytest -v

# Run a specific test file
pytest tests/test_comments.py
```

---

## 📡 API Documentation & Endpoints

Once the application is running, access the interactive auto-generated documentation:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Summary of Routers (`/api/v1`)

| Router | Base Route | Key Operations |
|---|---|---|
| **Auth** | `/api/v1/auth` | Login, Register, Token Refresh, Password Reset, Google SSO |
| **Users** | `/api/v1/users` | Profile view, Profile update, Change password, Delete account |
| **Products** | `/api/v1/products` | Search, Category filter, Price range, Product CRUD |
| **Orders** | `/api/v1/orders` | Create order, Checkout, User history, Track order code |
| **Comments** | `/api/v1/comments` | Submit product reviews, List approved comments, Moderation |
| **Addresses** | `/api/v1/addresses` | Manage delivery addresses, set default address |
| **Wishlist & Favorites** | `/api/v1/favorites`, `/api/v1/wishlist` | Save/unsave favorite art items |
| **Blog & FAQs** | `/api/v1/blog`, `/api/v1/faqs` | Read blog articles and FAQs |
| **Banners** | `/api/v1/banners` | Home hero banner carousel images |
| **Uploads** | `/api/v1/uploads` | Upload media files to cloud blob storage |
| **Admin** | `/api/v1/admin` | Admin dashboard analytics, user permissions, order management |

---

## 🌐 Deployment

### Deploying to Vercel

The backend includes a `vercel.json` configuration file ready for serverless deployment:

1. Install the Vercel CLI: `npm i -g vercel`
2. Run `vercel` from the `backend/` directory.
3. Configure environment variables in the Vercel dashboard (`MONGODB_URI`, `SECRET_KEY`, etc.).

---

## 📄 License

Proprietary and confidential. All rights reserved by **Artisa**.
