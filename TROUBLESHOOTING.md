# Troubleshooting Guide

## MongoDB Connection Issues

### DNS Resolution Timeout Error

**Error Message:**
```
pymongo.errors.ConfigurationError: The resolution lifetime expired after 21.606 seconds
```

**Cause:** Your DNS server cannot resolve MongoDB Atlas SRV records (`mongodb+srv://`).

**Solution:** Use the standard MongoDB connection string instead of SRV format.

### How to Get Standard Connection String

1. **Go to MongoDB Atlas Dashboard**
   - Visit https://cloud.mongodb.com/
   - Select your cluster

2. **Get Connection String**
   - Click "Connect" button
   - Choose "Connect your application"
   - Select "Python" and version "3.12 or later"
   - Copy the connection string

3. **Convert to Standard Format**
   
   If you have an SRV string like:
   ```
   mongodb+srv://username:password@cluster0.bnltfut.mongodb.net/
   ```
   
   You need to convert it to standard format. MongoDB Atlas provides this in the connection dialog.
   
   Standard format looks like:
   ```
   mongodb://username:password@host1:27017,host2:27017,host3:27017/?replicaSet=xxx&authSource=admin&retryWrites=true&w=majority&ssl=true
   ```

4. **Update Your .env File**
   
   Replace the MONGODB_URI in your `.env` file with the standard connection string.
   
   **IMPORTANT:** Make sure to URL-encode your password!
   
   Use the `encode_password.py` script:
   ```bash
   python encode_password.py
   ```

### Alternative: Use Direct IP Addresses

If DNS continues to fail, you can use IP addresses directly:

1. Find your cluster's IP addresses from MongoDB Atlas
2. Use them in the connection string instead of hostnames

### Network Troubleshooting

1. **Check Firewall**
   - Ensure port 27017 is not blocked
   - Check if your organization's firewall allows MongoDB Atlas connections

2. **Check VPN/Proxy**
   - Disable VPN temporarily to test
   - Configure proxy settings if required

3. **Check MongoDB Atlas IP Whitelist**
   - Go to MongoDB Atlas → Network Access
   - Add your current IP address or use `0.0.0.0/0` for testing (not recommended for production)

4. **Test Connection**
   ```bash
   # Test if you can reach MongoDB Atlas
   ping cluster0-shard-00-00.bnltfut.mongodb.net
   
   # Test port connectivity
   telnet cluster0-shard-00-00.bnltfut.mongodb.net 27017
   ```

### Using Google DNS

If your DNS server is unreliable, try using Google's public DNS:

**Windows:**
1. Open Network Connections
2. Right-click your network adapter → Properties
3. Select "Internet Protocol Version 4 (TCP/IPv4)" → Properties
4. Use these DNS servers:
   - Preferred: `8.8.8.8`
   - Alternate: `8.8.4.4`

**Linux/Mac:**
Edit `/etc/resolv.conf`:
```
nameserver 8.8.8.8
nameserver 8.8.4.4
```

### Still Having Issues?

1. **Check MongoDB Atlas Status**
   - Visit https://status.mongodb.com/

2. **Contact Support**
   - MongoDB Atlas Support: https://support.mongodb.com/
   - Check MongoDB Community Forums

3. **Use Local MongoDB for Development**
   - Install MongoDB locally
   - Update MONGODB_URI to: `mongodb://localhost:27017/`

## Other Common Issues

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Environment Variables Not Loading

**Error:** `KeyError: 'SECRET_KEY'`

**Solution:**
1. Ensure `.env` file exists in the project root
2. Check that all required variables are set
3. Restart the application

### Port Already in Use

**Error:** `OSError: [Errno 98] Address already in use`

**Solution:**
```bash
# Find process using port 8000
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Kill the process or use a different port
uvicorn main:app --reload --port 8001
```

### JWT Token Issues

**Error:** `Could not validate credentials`

**Solution:**
1. Check that SECRET_KEY is set correctly
2. Ensure token hasn't expired
3. Verify token format: `Bearer <token>`

## Need More Help?

Create an issue on GitHub with:
- Error message
- Steps to reproduce
- Your environment (OS, Python version)
- Relevant logs