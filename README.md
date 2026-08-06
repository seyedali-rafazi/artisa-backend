# Artisa Backend API

Production-ready RESTful API backend for **Artisa (آرتیسا)** — Iranian online art gallery and e-commerce platform. Built with **FastAPI**, **MongoDB** (Beanie ODM), **JWT Authentication**, and deployable to **Vercel**.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Running the Server](#running-the-server)
  - [Seeding Initial Data](#seeding-initial-data)
- [API Overview](#api-overview)
- [Collections](#collections)

---

## Features

- **Product Catalog & Management** — Search, category filter, amazing offers (`isSpecial`), best sellers (`isBestSeller`), price range filter, multi-field sorting, and pagination.
- **Product Reviews & Comments** — Read and submit reviews and star ratings.
- **User Authentication** — JWT access + refresh tokens, secure password hashing (`bcrypt`), login, register, and logout.
- **User Profile & Security** — Profile updates, password changes, and account deletion.
- **Saved Addresses** — Add, edit, delete, and set default shipping addresses.
- **Orders & Tracking** — Checkout order creation, user order history, and public order status tracking by order number.
- **Wishlist** — Personal wishlist management.
- **Blog & FAQs** — Blog articles and frequently asked questions.
- **Home Hero Banners** — Dynamic banner carousel config.
- **Image Uploads** — File upload router with static file serving.
- **Standard API Envelope** — All responses return `{ "success": true/false, "message": "...", "data": ... }`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.109 |
| Server | Uvicorn 0.27 |
| Database | MongoDB Atlas |
| Async Driver | Motor 3.3 |
| ODM | Beanie 1.24 |
| Auth | python-jose (JWT HS256) + passlib (bcrypt) |
| Validation | Pydantic v2 |
| Config | python-decouple |
| Python | 3.12 |

---

## Project Structure

```
backend/
├── main.py                          # Application entry point, routers & middleware
├── seed_data.py                     # Initial database seeder script
├── requirements.txt                 # Dependencies
├── API_DOCUMENTATION.md             # Complete API documentation
├── Artisa.postman_collection.json   # Postman API Collection
├── bruno/                           # Bruno API Collection
│   └── collection.json
├── core/
│   ├── config.py                    # Settings (python-decouple)
│   ├── database.py                  # Motor + Beanie initialization
│   └── security.py                  # JWT authentication & security helpers
├── models/
│   ├── user.py                      # User document
│   ├── product.py                   # Product document
│   ├── comment.py                   # Product Comment document
│   ├── address.py                   # Address document
│   ├── order.py                     # Order document
│   ├── wishlist.py                  # Wishlist document
│   ├── blog.py                      # Blog Article document
│   ├── faq.py                       # FAQ document
│   └── banner.py                    # Hero Banner document
├── api/
│   └── v1/
│       ├── auth.py                  # Authentication routes
│       ├── users.py                 # Profile & user management routes
│       ├── products.py              # Products search, filter & CRUD
│       ├── comments.py              # Product reviews
│       ├── addresses.py             # Saved addresses
│       ├── orders.py                # Orders & tracking
│       ├── wishlist.py              # User wishlist
│       ├── blog.py                  # Blog articles
│       ├── faqs.py                  # FAQs
│       ├── banners.py               # Home hero slider banners
│       └── uploads.py               # Image file upload
└── schemas/                         # Pydantic request & response DTOs
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- MongoDB instance (MongoDB Atlas or local MongoDB)

### Installation

```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate      # Linux / macOS

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
DEBUG=True
SECRET_KEY=your-random-secret-key
MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.bnltfut.mongodb.net/
DATABASE_NAME=artisa_db
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Running the Server

```bash
# Start development server
uvicorn main:app --reload --port 8000
```

Interactive Swagger UI documentation: `http://localhost:8000/docs`

### Seeding Initial Data

```bash
python seed_data.py
```

---

## Collections

- **Postman Collection**: `Artisa.postman_collection.json`
- **Bruno Collection**: `bruno/collection.json`
