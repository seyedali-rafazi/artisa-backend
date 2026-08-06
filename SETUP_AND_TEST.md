# Backend Setup and Testing Guide

## Quick Setup Steps

### 1. Install Python Dependencies

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file from `.env.example`:
```bash
copy .env.example .env
```

Edit `.env` and add your MongoDB password:
```env
MONGODB_PASSWORD=your_actual_mongodb_password_here
```

### 3. Initialize Database

```bash
python manage.py migrate
python manage.py createsuperuser
```

Follow prompts to create admin user.

### 4. Run Server

```bash
python manage.py runserver
```

Server will start at: `http://localhost:8000`

---

## Testing the API

### Method 1: Using cURL

#### 1. Register a User
```bash
curl -X POST http://localhost:8000/api/auth/register/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@example.com\",\"password\":\"Test123456\",\"password2\":\"Test123456\",\"first_name\":\"Test\",\"last_name\":\"User\",\"phone\":\"+1234567890\"}"
```

#### 2. Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@example.com\",\"password\":\"Test123456\"}"
```

Save the `access` token from response.

#### 3. Get Profile (with token)
```bash
curl -X GET http://localhost:8000/api/auth/profile/ ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

#### 4. Get Cities
```bash
curl -X GET http://localhost:8000/api/flights/cities/
```

#### 5. Search Flights
```bash
curl -X POST http://localhost:8000/api/flights/search/ ^
  -H "Content-Type: application/json" ^
  -d "{\"origin\":\"THR\",\"destination\":\"MHD\",\"departure_date\":\"2024-12-25\",\"passengers\":1,\"flight_class\":\"economy\"}"
```

### Method 2: Using Python

Create a test file `test_api.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

# 1. Register
register_data = {
    "email": "test@example.com",
    "password": "Test123456",
    "password2": "Test123456",
    "first_name": "Test",
    "last_name": "User",
    "phone": "+1234567890"
}

response = requests.post(f"{BASE_URL}/auth/register/", json=register_data)
print("Register:", response.status_code)
print(json.dumps(response.json(), indent=2))

# 2. Login
login_data = {
    "email": "test@example.com",
    "password": "Test123456"
}

response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
print("\nLogin:", response.status_code)
data = response.json()
print(json.dumps(data, indent=2))

# Save token
access_token = data['tokens']['access']
headers = {"Authorization": f"Bearer {access_token}"}

# 3. Get Profile
response = requests.get(f"{BASE_URL}/auth/profile/", headers=headers)
print("\nProfile:", response.status_code)
print(json.dumps(response.json(), indent=2))

# 4. Get Cities
response = requests.get(f"{BASE_URL}/flights/cities/")
print("\nCities:", response.status_code)
print(json.dumps(response.json(), indent=2))

# 5. Search Flights
search_data = {
    "origin": "THR",
    "destination": "MHD",
    "departure_date": "2024-12-25",
    "passengers": 1,
    "flight_class": "economy"
}

response = requests.post(f"{BASE_URL}/flights/search/", json=search_data)
print("\nFlight Search:", response.status_code)
print(json.dumps(response.json(), indent=2))
```

Run:
```bash
python test_api.py
```

### Method 3: Using Postman

1. Import the API endpoints from `API_DOCUMENTATION.md`
2. Create a new environment with:
   - `base_url`: `http://localhost:8000/api`
   - `access_token`: (will be set after login)

3. Test sequence:
   - POST `/auth/register/`
   - POST `/auth/login/` → Save access token
   - GET `/auth/profile/` (with Bearer token)
   - GET `/flights/cities/`
   - POST `/flights/search/`

---

## Adding Sample Data via Admin Panel

1. Go to `http://localhost:8000/admin/`
2. Login with superuser credentials
3. Add sample data:

### Add Cities
- Code: THR, Name: Tehran
- Code: MHD, Name: Mashhad
- Code: ISF, Name: Isfahan
- Code: SYZ, Name: Shiraz

### Add Flights
- Airline: Iran Air
- Flight Number: IR123
- Origin: THR
- Destination: MHD
- Departure Time: 2024-12-25 10:00:00
- Arrival Time: 2024-12-25 11:30:00
- Duration: 1h 30m
- Price: 1500000
- Available Seats: 50
- Flight Class: economy
- Features: ["Meal", "WiFi"]

### Add Popular Flights
- From: Tehran, To: Mashhad
- From Code: THR, To Code: MHD
- Price: از ۱,۵۰۰,۰۰۰ تومان

### Add Insurance Plans
- Title: Basic Travel Insurance
- Price: 200000
- Coverage: Up to $50,000
- Features: ["Medical Coverage", "Trip Cancellation"]

### Add Transport Trips
- Transport Type: bus
- Company: Iran Peyma
- Trip Number: IP123
- Origin: Tehran
- Destination: Isfahan
- Price: 500000
- Available Seats: 30

---

## Testing Checklist

### Authentication
- [ ] User registration works
- [ ] User login returns JWT tokens
- [ ] Token refresh works
- [ ] Protected endpoints require authentication
- [ ] User profile retrieval works
- [ ] Password change works

### Flights
- [ ] Cities list is accessible
- [ ] Flight search returns results
- [ ] Flight details are retrievable
- [ ] Popular flights are listed
- [ ] Destinations are listed

### Transport
- [ ] Transport search works for bus
- [ ] Transport search works for train
- [ ] Transport details are retrievable

### Insurance
- [ ] Insurance plans are listed
- [ ] Insurance booking creation works
- [ ] Tracking code is generated
- [ ] Booking retrieval by tracking code works

### Bookings
- [ ] Flight booking creation works
- [ ] Transport booking creation works
- [ ] User bookings are listed
- [ ] Booking cancellation works
- [ ] Tracking code lookup works

---

## Common Issues and Solutions

### Issue: ModuleNotFoundError
**Solution:** Activate virtual environment and install dependencies
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: MongoDB Connection Error
**Solution:** 
1. Check `.env` file has correct password
2. Verify MongoDB Atlas IP whitelist
3. Test connection string in MongoDB Compass

### Issue: Migration Errors
**Solution:**
```bash
python manage.py makemigrations
python manage.py migrate --run-syncdb
```

### Issue: CORS Errors from Frontend
**Solution:** Add frontend URL to `.env`:
```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Issue: JWT Token Expired
**Solution:** Use refresh token to get new access token:
```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ ^
  -H "Content-Type: application/json" ^
  -d "{\"refresh\":\"YOUR_REFRESH_TOKEN\"}"
```

---

## Next Steps

After backend is tested and working:

1. **Frontend Integration:**
   - Update frontend API calls to use backend endpoints
   - Replace mock data with real API calls
   - Implement token storage and refresh logic

2. **Production Deployment:**
   - Set up production MongoDB
   - Configure production settings
   - Deploy to hosting service (Heroku, AWS, etc.)

3. **Additional Features:**
   - Email notifications
   - Payment gateway integration
   - PDF ticket generation
   - SMS notifications

---

## API Testing Tools

Recommended tools for testing:
- **Postman** - GUI-based API testing
- **Insomnia** - Alternative to Postman
- **HTTPie** - Command-line HTTP client
- **cURL** - Built-in command-line tool
- **Python requests** - Programmatic testing

---

## Support

For detailed API documentation, see `API_DOCUMENTATION.md`
For setup instructions, see `README.md`