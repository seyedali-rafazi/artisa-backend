# Billito — Aircraft Tickets API

A production-ready REST API backend for an Iranian travel ticketing platform, supporting flights, bus/train trips, travel insurance, and bookings. Built with **FastAPI**, **MongoDB**, and deployable to **Vercel**.

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
- [API Overview](#api-overview)
  - [Authentication](#authentication)
  - [Endpoints](#endpoints)
- [Data Models](#data-models)
- [Deployment (Vercel)](#deployment-vercel)
- [Troubleshooting](#troubleshooting)

---

## Features

- **Flight Search & Booking** — search by origin, destination, date, passengers, and class
- **Bus & Train Trips** — unified transport search across bus and train
- **Travel Insurance** — browse plans and purchase with tracking code
- **JWT Authentication** — access + refresh token flow with bcrypt password hashing
- **Admin Panel** — protected admin routes for managing flights, trips, and plans
- **Guest Bookings** — bookings and insurance purchases work without an account
- **Interactive API Docs** — auto-generated Swagger UI at `/docs`
- **Vercel Serverless** — zero-config deployment via `@vercel/python`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.109 |
| Server | Uvicorn 0.27 |
| Database | MongoDB Atlas |
| Async Driver | Motor 3.3 |
| ODM | Beanie 1.24 |
| Auth | python-jose (JWT HS256) + bcrypt |
| Validation | Pydantic v2 |
| Config | python-decouple |
| Deployment | Vercel (`@vercel/python`) |
| Python | 3.12 |

---

## Project Structure

```
backend/
├── main.py                  # Application entry point, routers, middleware
├── requirements.txt         # Pinned dependencies
├── vercel.json              # Vercel deployment config
├── manage.py                # CLI helper (migrate, createsuperuser, runserver)
├── core/
│   ├── config.py            # Settings (env-driven via python-decouple)
│   ├── database.py          # Motor + Beanie initialization
│   └── security.py          # JWT helpers and auth dependencies
├── models/
│   ├── user.py              # User document
│   ├── flight.py            # Flight, City, PopularFlight, Destination documents
│   ├── booking.py           # Booking document
│   ├── insurance.py         # Insurance, InsuranceBooking documents
│   └── transport.py         # TransportTrip, TransportRoute documents
├── api/
│   └── v1/
│       ├── users.py         # Auth & profile routes
│       ├── flights.py       # Flight search & management routes
│       ├── bookings.py      # Booking routes
│       ├── transport.py     # Bus/train routes
│       ├── insurance.py     # Insurance routes
│       └── admin.py         # Admin-only routes
├── schemas/                 # Pydantic request/response schemas
└── apps/                    # Legacy Django-style app scaffolding (not active)
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- A [MongoDB Atlas](https://www.mongodb.com/atlas) cluster (free tier works)

### Installation

```bash
# Clone the repository and navigate to the backend
cd backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate      # Linux / macOS

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the `backend/` directory. All required variables are listed below:

```env
# Application
SECRET_KEY=your-random-secret-key   # Generate: openssl rand -hex 32
DEBUG=True

# MongoDB
MONGODB_URI=mongodb+srv://<username>:<db_password>@cluster0.bnltfut.mongodb.net/
MONGODB_NAME=aircraft_tickets
MONGODB_PASSWORD=your-mongo-password  # Used to substitute <db_password> in URI

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60          # Minutes (default: 60)
JWT_REFRESH_TOKEN_LIFETIME=1440       # Minutes (default: 1440 = 24 hours)

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

> **Tip:** If your MongoDB password contains special characters, run `python encode_password.py` to URL-encode it before placing it in the URI.

### Running the Server

```bash
# Run database migrations and create a superuser
python manage.py migrate
python manage.py createsuperuser

# Start the development server
python manage.py runserver
# or directly:
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive Swagger docs: `http://localhost:8000/docs`

---

## API Overview

**Base URL:** `http://localhost:8000/api/v1` (local) or `https://<your-project>.vercel.app/api/v1` (production)

### Authentication

The API uses **JWT Bearer tokens**.

```
Authorization: Bearer <access_token>
```

| Token | TTL |
|---|---|
| Access token | 60 minutes |
| Refresh token | 24 hours |

Obtain tokens via `POST /api/v1/users/auth/login/`. Refresh via `POST /api/v1/users/auth/token/refresh/`.

---

### Endpoints

#### Users & Auth — `/api/v1/users/auth/`

| Method | Path | Auth Required | Description |
|---|---|---|---|
| POST | `/auth/register/` | No | Register a new user |
| POST | `/auth/login/` | No | Login, returns access + refresh tokens |
| POST | `/auth/logout/` | Yes | Logout (invalidate refresh token) |
| POST | `/auth/token/refresh/` | No | Get a new access token |
| GET | `/auth/profile/` | Yes | Get current user profile |
| PUT/PATCH | `/auth/profile/` | Yes | Update name or phone |
| POST | `/auth/change-password/` | Yes | Change password |

#### Flights — `/api/v1/flights/`

| Method | Path | Auth Required | Description |
|---|---|---|---|
| GET | `/cities/` | No | List all cities (IATA code, name, country) |
| POST | `/search/` | No | Search flights by origin, destination, date, passengers, class |
| GET | `/<id>/` | No | Flight detail |
| GET | `/popular/` | No | Popular routes with prices |
| GET | `/destinations/` | No | Popular destinations |
| GET | `/` | No | List all flights |
| POST | `/` | Admin | Create a flight |
| PUT/PATCH/DELETE | `/<id>/manage/` | Admin | Update or delete a flight |

#### Transport (Bus & Train) — `/api/v1/transport/`

| Method | Path | Auth Required | Description |
|---|---|---|---|
| POST | `/search/` | No | Search bus/train trips |
| GET | `/<id>/` | No | Trip detail |
| GET | `/` | No | List all trips |
| POST | `/` | Admin | Create a trip |
| PUT/PATCH/DELETE | `/<id>/manage/` | Admin | Update or delete a trip |

#### Insurance — `/api/v1/insurance/`

| Method | Path | Auth Required | Description |
|---|---|---|---|
| GET | `/plans/` | No | List all insurance plans |
| GET | `/plans/<id>/` | No | Plan detail |
| POST | `/bookings/` | No | Purchase an insurance plan, returns tracking code |
| GET | `/my-bookings/` | Yes | User's insurance bookings |
| GET | `/bookings/<tracking_code>/` | No | Look up by tracking code |

#### Bookings — `/api/v1/bookings/`

| Method | Path | Auth Required | Description |
|---|---|---|---|
| POST | `/create/` | No | Create a flight or bus/train booking |
| GET | `/my-bookings/` | Yes | User's bookings |
| GET | `/my-tickets/` | Yes | All user tickets |
| GET | `/<tracking_code>/` | No | Look up booking by tracking code |
| POST | `/<tracking_code>/cancel/` | Yes | Cancel a booking |

#### Utility

| Method | Path | Description |
|---|---|---|
| GET | `/` | API name, version, and docs link |
| GET | `/health` | Health check — `{"status": "healthy"}` |

---

### Error Responses

| Status | Description |
|---|---|
| 400 | Bad Request — `{"error": "...", "details": {"field": [...]}}` |
| 401 | Unauthorized — `{"detail": "Authentication credentials were not provided."}` |
| 404 | Not Found — `{"error": "Resource not found"}` |
| 500 | Internal Server Error |

---

## Data Models

### User
Fields: `email` (unique), `first_name`, `last_name`, `phone`, `hashed_password`, `is_active`, `is_staff`, `is_superuser`, `date_joined`, `last_login`

### Flight
Fields: `airline`, `flight_number`, `origin`, `destination` (IATA codes), `departure_time`, `arrival_time`, `duration`, `price` (IRR), `available_seats`, `stops`, `flight_class` (`economy` / `business` / `first`), `features`, `is_active`

### TransportTrip
Fields: `transport_type` (`bus` / `train`), `company`, `trip_number`, `origin`, `destination`, `departure_time`, `arrival_time`, `duration`, `price` (IRR), `available_seats`, `features`

### Booking
Fields: `booking_type` (`flight` / `bus` / `train`), `passengers` (list with name, national ID, birth date, gender), `contact_email`, `contact_phone`, `tracking_code` (10-char alphanumeric), `total_price`, `status` (`pending` / `confirmed` / `cancelled`), `seat_numbers`

### Insurance / InsuranceBooking
Plan fields: `title`, `price` (IRR), `coverage`, `popular`, `features`  
Booking fields: `plan_id`, `first_name`, `last_name`, `national_id`, `birth_date`, `destination`, `start_date`, `end_date`, `tracking_code`, `status`

> All prices are in **Iranian Rials (IRR)**. All datetimes are **ISO 8601 UTC**. Tracking codes are unique **10-character alphanumeric** strings.

---

## Deployment (Vercel)

### 1. Install Vercel CLI

```bash
npm install -g vercel
```

### 2. Set Environment Variables

In the [Vercel Dashboard](https://vercel.com) under your project's **Settings → Environment Variables**, add all variables from the [Environment Variables](#environment-variables) section above. For production, ensure:

- `DEBUG=False`
- `SECRET_KEY` is a strong random value
- `CORS_ALLOWED_ORIGINS` lists only your actual frontend domain(s)
- MongoDB Atlas **Network Access** allows `0.0.0.0/0` (for Vercel's dynamic IPs)

### 3. Deploy

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

Or connect your GitHub/GitLab repository in the Vercel Dashboard for automatic deployments on push.

### 4. Verify

```bash
curl https://your-project.vercel.app/health
# {"status": "healthy"}
```

Swagger docs: `https://your-project.vercel.app/docs`

### Vercel Limitations

| Limitation | Detail |
|---|---|
| Timeout | 10 s (Hobby) / 60 s (Pro) |
| Cold starts | First request may be slow |
| WebSockets | Not supported on Hobby plan |
| State | Stateless — no persistent local storage between requests |

---

## Troubleshooting

### MongoDB Connection Fails

- **Atlas IP whitelist:** Add `0.0.0.0/0` (development) or your server's IP (production) in Atlas → Network Access.
- **SRV DNS timeout:** Replace `mongodb+srv://...` with the direct connection string from Atlas (standard `mongodb://host1,host2,host3/?replicaSet=...`).
- **Special characters in password:** Run `python encode_password.py` and use the encoded value in `MONGODB_URI`.
- **Test connectivity:**
  ```bash
  ping cluster0-shard-00-00.bnltfut.mongodb.net
  telnet cluster0-shard-00-00.bnltfut.mongodb.net 27017
  ```

### Common Errors

| Error | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | Activate the virtual environment, then `pip install -r requirements.txt` |
| `KeyError: 'SECRET_KEY'` | Ensure `.env` exists with all required variables and restart the server |
| `Address already in use` (port 8000) | Run on a different port: `uvicorn main:app --reload --port 8001` |
| `Could not validate credentials` | Verify `SECRET_KEY` matches, token is not expired, and header format is `Bearer <token>` |
| CORS errors in browser | Add the frontend origin to `CORS_ALLOWED_ORIGINS` in `.env` |
| JWT expired | `POST /api/v1/users/auth/token/refresh/` with your refresh token |

---

## Generating a Secret Key

```bash
python generate_secret_key.py
# or
openssl rand -hex 32
```

---

## License

This project is private. All rights reserved.
