# Deploying FastAPI to Vercel

## Prerequisites
- Vercel account (https://vercel.com)
- Vercel CLI installed: `npm install -g vercel`
- Git repository

## Step 1: Prepare Your Project

Your project is already configured with `vercel.json`. Make sure all files are committed to git.

## Step 2: Set Environment Variables in Vercel

You need to add your environment variables to Vercel:

### Via Vercel Dashboard:
1. Go to https://vercel.com/dashboard
2. Select your project (or import it)
3. Go to **Settings** → **Environment Variables**
4. Add these variables:

```
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=False
MONGODB_URI=mongodb+srv://rfzali93:25%25jA%2Bx%2AfJes6Zu@cluster0.bnltfut.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
MONGODB_NAME=aircraft_tickets
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app,http://localhost:3000
```

### Via Vercel CLI:
```bash
vercel env add SECRET_KEY
vercel env add MONGODB_URI
vercel env add MONGODB_NAME
vercel env add JWT_ACCESS_TOKEN_LIFETIME
vercel env add JWT_REFRESH_TOKEN_LIFETIME
vercel env add CORS_ALLOWED_ORIGINS
```

## Step 3: Deploy to Vercel

### Option A: Deploy via Vercel CLI
```bash
# Login to Vercel
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

### Option B: Deploy via Git Integration
1. Push your code to GitHub/GitLab/Bitbucket
2. Go to https://vercel.com/new
3. Import your repository
4. Vercel will auto-detect FastAPI and deploy

## Step 4: Test Your Deployment

Once deployed, Vercel will give you a URL like: `https://your-project.vercel.app`

Test your endpoints:
```bash
# Test root endpoint
curl https://your-project.vercel.app/

# Test health check
curl https://your-project.vercel.app/health

# Test API docs
# Visit: https://your-project.vercel.app/docs
```

## Step 5: Test with Postman

1. **Open Postman**

2. **Test Root Endpoint**:
   - Method: GET
   - URL: `https://your-project.vercel.app/`
   - Expected: `{"message": "Aircraft Tickets API", "version": "1.0.0", "docs": "/docs"}`

3. **Register a User**:
   - Method: POST
   - URL: `https://your-project.vercel.app/api/v1/users/register`
   - Headers: `Content-Type: application/json`
   - Body (raw JSON):
   ```json
   {
     "email": "test@example.com",
     "password": "testpassword123",
     "first_name": "Test",
     "last_name": "User",
     "phone": "+1234567890"
   }
   ```

4. **Login**:
   - Method: POST
   - URL: `https://your-project.vercel.app/api/v1/users/login`
   - Headers: `Content-Type: application/json`
   - Body (raw JSON):
   ```json
   {
     "email": "test@example.com",
     "password": "testpassword123"
   }
   ```
   - Copy the `access_token` from response

5. **Get Current User** (Protected Route):
   - Method: GET
   - URL: `https://your-project.vercel.app/api/v1/users/me`
   - Headers:
     - `Content-Type: application/json`
     - `Authorization: Bearer YOUR_ACCESS_TOKEN_HERE`

6. **Search Flights**:
   - Method: GET
   - URL: `https://your-project.vercel.app/api/v1/flights/search?origin=JFK&destination=LAX&flight_class=economy`

## Important Notes

### CORS Configuration
Make sure to update `CORS_ALLOWED_ORIGINS` in Vercel environment variables to include:
- Your frontend domain
- Postman (for testing): You can use `*` for development, but specify exact origins in production

### MongoDB Atlas Network Access
1. Go to MongoDB Atlas → Network Access
2. Add Vercel's IP addresses or use `0.0.0.0/0` (allow from anywhere)
   - **Note**: `0.0.0.0/0` is less secure but easier for serverless deployments

### Vercel Limitations
- **Cold starts**: First request may be slow
- **Execution timeout**: 10 seconds for Hobby plan, 60 seconds for Pro
- **No WebSocket support** on Hobby plan
- **Stateless**: Each request is independent

### Debugging Deployment Issues

1. **Check Vercel Logs**:
   ```bash
   vercel logs
   ```

2. **Check Build Logs** in Vercel Dashboard

3. **Common Issues**:
   - Missing environment variables
   - MongoDB connection timeout
   - CORS errors
   - Import errors

## Production Checklist

- [ ] Set `DEBUG=False` in Vercel environment variables
- [ ] Use strong `SECRET_KEY` (generate with `openssl rand -hex 32`)
- [ ] Configure proper CORS origins (no wildcards)
- [ ] Set up MongoDB Atlas IP whitelist
- [ ] Test all endpoints
- [ ] Set up custom domain (optional)
- [ ] Enable Vercel Analytics (optional)

## Postman Collection

Create a Postman collection with these requests:

### Collection Structure:
```
Aircraft Tickets API
├── Health Check (GET /health)
├── Root (GET /)
├── Users
│   ├── Register (POST /api/v1/users/register)
│   ├── Login (POST /api/v1/users/login)
│   ├── Get Profile (GET /api/v1/users/me)
│   └── Update Profile (PUT /api/v1/users/me)
├── Flights
│   ├── Search Flights (GET /api/v1/flights/search)
│   ├── Get Flight (GET /api/v1/flights/{id})
│   ├── Popular Routes (GET /api/v1/flights/popular/routes)
│   └── Popular Destinations (GET /api/v1/flights/destinations/popular)
├── Bookings
│   ├── Create Booking (POST /api/v1/bookings/)
│   ├── My Bookings (GET /api/v1/bookings/my-bookings)
│   ├── Track Booking (GET /api/v1/bookings/track/{code})
│   └── Cancel Booking (PUT /api/v1/bookings/{id}/cancel)
├── Transport
│   ├── Search Transport (GET /api/v1/transport/search)
│   └── Popular Routes (GET /api/v1/transport/routes/popular)
└── Insurance
    ├── Get Plans (GET /api/v1/insurance/plans)
    ├── Create Booking (POST /api/v1/insurance/bookings)
    └── Track Booking (GET /api/v1/insurance/bookings/track/{code})
```

### Environment Variables in Postman:
- `base_url`: `https://your-project.vercel.app`
- `access_token`: (set after login)

## Support

If you encounter issues:
1. Check Vercel deployment logs
2. Verify environment variables are set correctly
3. Test MongoDB connection from Vercel
4. Check CORS configuration
5. Review Vercel function logs

## Next Steps

After successful deployment:
1. Update your frontend to use the Vercel API URL
2. Set up monitoring (Vercel Analytics, Sentry, etc.)
3. Configure custom domain
4. Set up CI/CD pipeline
5. Add rate limiting for production