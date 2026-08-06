# Aircraft Tickets API - FastAPI + MongoDB Atlas + Beanie

A modern REST API for aircraft ticket booking system built with FastAPI, MongoDB Atlas, and Beanie ODM.

## 🚀 Tech Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **MongoDB Atlas** - Cloud-hosted MongoDB database
- **Beanie** - Async Python ODM for MongoDB
- **Motor** - Async MongoDB driver
- **Pydantic** - Data validation using Python type annotations
- **JWT** - JSON Web Tokens for authentication
- **Uvicorn** - ASGI server

## 📋 Prerequisites

- Python 3.8+
- MongoDB Atlas account
- pip or poetry for package management

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**

Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# Generate secret key: openssl rand -hex 32
SECRET_KEY=your-secret-key-here

# MongoDB Atlas credentials
MONGODB_URI=mongodb+srv://username:<db_password>@cluster.mongodb.net/
MONGODB_PASSWORD=your-mongodb-password
MONGODB_NAME=aircraft_tickets

# JWT settings (in minutes)
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Debug mode
DEBUG=True
```

## 🏃 Running the Application

### Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc

## 📁 Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .env                   # Environment variables (create this)
│
├── core/                  # Core application modules
│   ├── __init__.py
│   ├── config.py         # Application configuration
│   ├── database.py       # Database connection and initialization
│   └── security.py       # Authentication and security utilities
│
├── models/               # Beanie ODM models
│   ├── __init__.py
│   ├── user.py          # User model
│   ├── flight.py        # Flight models
│   ├── booking.py       # Booking model
│   ├── transport.py     # Transport models
│   └── insurance.py     # Insurance models
│
├── schemas/             # Pydantic schemas for validation
│   ├── __init__.py
│   └── user.py         # User schemas
│
└── api/                # API routes
    └── v1/             # API version 1
        ├── __init__.py
        ├── users.py        # User endpoints
        ├── flights.py      # Flight endpoints
        ├── bookings.py     # Booking endpoints
        ├── transport.py    # Transport endpoints
        └── insurance.py    # Insurance endpoints
```

## 🔑 API Endpoints

### Authentication
- `POST /api/v1/users/register` - Register new user
- `POST /api/v1/users/login` - Login user
- `GET /api/v1/users/me` - Get current user info
- `PUT /api/v1/users/me` - Update current user

### Flights
- `GET /api/v1/flights/search` - Search flights
- `GET /api/v1/flights/{flight_id}` - Get flight details
- `GET /api/v1/flights/popular/routes` - Get popular routes
- `GET /api/v1/flights/destinations/popular` - Get popular destinations
- `GET /api/v1/flights/cities/search` - Search cities
- `GET /api/v1/flights/cities/all` - Get all cities

### Bookings
- `POST /api/v1/bookings/` - Create booking
- `GET /api/v1/bookings/my-bookings` - Get user's bookings
- `GET /api/v1/bookings/track/{tracking_code}` - Track booking
- `GET /api/v1/bookings/{booking_id}` - Get booking details
- `PUT /api/v1/bookings/{booking_id}/cancel` - Cancel booking

### Transport
- `GET /api/v1/transport/search` - Search transport trips
- `GET /api/v1/transport/{trip_id}` - Get trip details
- `GET /api/v1/transport/routes/popular` - Get popular routes

### Insurance
- `GET /api/v1/insurance/plans` - Get insurance plans
- `GET /api/v1/insurance/plans/{plan_id}` - Get plan details
- `POST /api/v1/insurance/bookings` - Create insurance booking
- `GET /api/v1/insurance/bookings/my-bookings` - Get user's insurance bookings
- `GET /api/v1/insurance/bookings/track/{tracking_code}` - Track insurance booking

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-access-token>
```

### Token Lifecycle
- **Access Token**: Valid for 60 minutes (configurable)
- **Refresh Token**: Valid for 24 hours (configurable)

## 📊 Database Models

### User
- Email-based authentication
- Password hashing with bcrypt
- Role-based access (user, staff, superuser)

### Flight
- Airline information
- Origin and destination
- Departure and arrival times
- Pricing and seat availability
- Flight class (economy, business, first)

### Booking
- User reference
- Flight or transport reference
- Passenger information
- Contact details
- Tracking code
- Booking status

### Transport
- Bus and train trips
- Route information
- Pricing and availability

### Insurance
- Insurance plans
- Coverage details
- Booking information

## 🧪 Testing

Access the interactive API documentation at http://localhost:8000/docs to test all endpoints.

## 🔧 Development

### Adding New Endpoints

1. Create a new router in `api/v1/`
2. Define your endpoints
3. Include the router in `main.py`

### Adding New Models

1. Create a new model in `models/`
2. Inherit from `beanie.Document`
3. Add the model to `core/database.py` initialization

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Secret key for JWT | Required |
| `DEBUG` | Debug mode | `True` |
| `MONGODB_URI` | MongoDB connection string | Required |
| `MONGODB_PASSWORD` | MongoDB password | Required |
| `MONGODB_NAME` | Database name | `aircraft_tickets` |
| `JWT_ACCESS_TOKEN_LIFETIME` | Access token lifetime (minutes) | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME` | Refresh token lifetime (minutes) | `1440` |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

## 🚀 Deployment

### Using Docker (Recommended)

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t aircraft-tickets-api .
docker run -p 8000:8000 --env-file .env aircraft-tickets-api
```

### Using Heroku

1. Create `Procfile`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

2. Deploy:
```bash
heroku create your-app-name
git push heroku main
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Beanie Documentation](https://beanie-odm.dev/)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Support

For support, email support@example.com or open an issue in the repository.