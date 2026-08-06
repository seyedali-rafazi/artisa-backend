# Fix Vercel Authentication Error

## The Problem
You're getting "bad auth : authentication failed" because the URL-encoded password in the connection string is being double-encoded by Vercel's environment variable system.

## The Solution

### Update Your Vercel Environment Variables:

1. **Go to Vercel Dashboard** → Your Project → Settings → Environment Variables

2. **Delete the current MONGODB_URI variable**

3. **Add these TWO variables instead:**

```
MONGODB_URI=mongodb+srv://rfzali93:<db_password>@cluster0.bnltfut.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
```

```
MONGODB_PASSWORD=25%jA+x*fJes6Zu
```

**IMPORTANT**: Use the RAW password (with `%`, `+`, `*` characters) in `MONGODB_PASSWORD`. The code will handle the URL encoding automatically.

### Why This Works:

The updated `core/config.py` now:
1. Takes the password from a separate environment variable
2. URL-encodes it properly using `quote_plus()`
3. Replaces `<db_password>` in the URI with the encoded password

This prevents double-encoding issues that occur when you put an already-encoded password in the URI.

## Step-by-Step Fix:

1. **In Vercel Dashboard:**
   - Go to Settings → Environment Variables
   - Add/Update these variables:
     ```
     MONGODB_URI = mongodb+srv://rfzali93:<db_password>@cluster0.bnltfut.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
     MONGODB_PASSWORD = 25%jA+x*fJes6Zu
     MONGODB_NAME = aircraft_tickets
     SECRET_KEY = your-secret-key-here
     JWT_ACCESS_TOKEN_LIFETIME = 60
     JWT_REFRESH_TOKEN_LIFETIME = 1440
     CORS_ALLOWED_ORIGINS = *
     DEBUG = False
     ```

2. **Redeploy:**
   ```bash
   vercel --prod
   ```

3. **Test:**
   ```bash
   curl https://your-app.vercel.app/health
   ```

## Alternative: Use Connection String Without Placeholder

If you prefer, you can also use the fully encoded connection string directly:

```
MONGODB_URI=mongodb+srv://rfzali93:25%25jA%2Bx%2AfJes6Zu@cluster0.bnltfut.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
```

And leave `MONGODB_PASSWORD` empty or don't set it.

## Verify MongoDB Atlas Settings:

1. **Network Access:**
   - Go to MongoDB Atlas → Network Access
   - Make sure `0.0.0.0/0` is whitelisted (or add Vercel's IP ranges)

2. **Database User:**
   - Go to Database Access
   - Verify user `rfzali93` exists
   - Verify password is correct: `25%jA+x*fJes6Zu`
   - Verify user has read/write permissions

## Test Locally First:

Update your local `.env` file to match:

```env
MONGODB_URI=mongodb+srv://rfzali93:<db_password>@cluster0.bnltfut.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
MONGODB_PASSWORD=25%jA+x*fJes6Zu
MONGODB_NAME=aircraft_tickets
```

Then test locally:
```bash
python -m uvicorn main:app --reload
```

If it works locally, deploy to Vercel with the same environment variables.

## Still Having Issues?

1. **Check Vercel Logs:**
   ```bash
   vercel logs
   ```

2. **Verify Environment Variables:**
   - Make sure all variables are set for "Production" environment
   - Check for typos in variable names

3. **Test MongoDB Connection:**
   Create a simple test script:
   ```python
   from pymongo import MongoClient
   from urllib.parse import quote_plus
   
   password = "25%jA+x*fJes6Zu"
   encoded = quote_plus(password)
   uri = f"mongodb+srv://rfzali93:{encoded}@cluster0.bnltfut.mongodb.net/"
   
   client = MongoClient(uri)
   print("Connected:", client.server_info())
   ```

4. **Contact MongoDB Atlas Support** if the credentials are definitely correct but still failing.