# Using Direct MongoDB Connection (No DNS Required)

Your network DNS cannot resolve MongoDB Atlas SRV records. You have two options:

## Option 1: Get Standard Connection String from MongoDB Atlas (RECOMMENDED)

1. **Go to MongoDB Atlas**: https://cloud.mongodb.com/
2. **Select your cluster** (cluster0)
3. **Click "Connect"**
4. **Choose "Connect your application"**
5. **Select Driver: Python, Version: 3.12 or later**
6. **IMPORTANT: Click "I want to use a different connection string format"**
7. **Select "Standard connection string"** (not SRV)
8. **Copy the connection string** - it will look like:
   ```
   mongodb://rfzali93:PASSWORD@cluster0-shard-00-00.bnltfut.mongodb.net:27017,cluster0-shard-00-01.bnltfut.mongodb.net:27017,cluster0-shard-00-02.bnltfut.mongodb.net:27017/?ssl=true&replicaSet=atlas-xxxxx-shard-0&authSource=admin&retryWrites=true&w=majority
   ```

9. **Encode your password** using the script:
   ```bash
   python encode_password.py
   ```
   
10. **Update your .env file** with the standard connection string

## Option 2: Use Local MongoDB for Development

If you can't access MongoDB Atlas due to network restrictions:

1. **Install MongoDB locally**:
   - Windows: https://www.mongodb.com/try/download/community
   - Mac: `brew install mongodb-community`
   - Linux: `sudo apt-get install mongodb`

2. **Start MongoDB**:
   ```bash
   # Windows
   mongod
   
   # Mac/Linux
   sudo systemctl start mongod
   ```

3. **Update your .env**:
   ```env
   MONGODB_URI=mongodb://localhost:27017/
   MONGODB_NAME=aircraft_tickets
   ```

## Option 3: Use MongoDB Atlas with VPN/Different Network

Your current network (192.168.43.1) is blocking MongoDB Atlas DNS resolution. Try:

1. **Use mobile hotspot** - Connect to your phone's internet
2. **Use VPN** - Try a different VPN service
3. **Use different network** - Try from a different location/WiFi
4. **Change DNS to Google DNS**:
   - Primary: 8.8.8.8
   - Secondary: 8.8.4.4

## Testing Your Connection

Once you have the standard connection string, test it:

```python
from pymongo import MongoClient

# Test connection
uri = "your-standard-connection-string-here"
client = MongoClient(uri)
print("Connected successfully!")
print("Databases:", client.list_database_names())
```

## Need the Standard Connection String?

If you can't access MongoDB Atlas dashboard, you can try these common formats:

### Format 1 (Most Common):
```
mongodb://rfzali93:25%25jA%2Bx%2AfJes6Zu@cluster0-shard-00-00.bnltfut.mongodb.net:27017,cluster0-shard-00-01.bnltfut.mongodb.net:27017,cluster0-shard-00-02.bnltfut.mongodb.net:27017/aircraft_tickets?ssl=true&replicaSet=atlas-abc123-shard-0&authSource=admin&retryWrites=true&w=majority
```

### Format 2 (Alternative):
```
mongodb://rfzali93:25%25jA%2Bx%2AfJes6Zu@ac-xxxxx-shard-00-00.bnltfut.mongodb.net:27017,ac-xxxxx-shard-00-01.bnltfut.mongodb.net:27017,ac-xxxxx-shard-00-02.bnltfut.mongodb.net:27017/aircraft_tickets?ssl=true&replicaSet=atlas-xxxxx-shard-0&authSource=admin
```

**Note**: You need to get the exact shard names and replica set name from your MongoDB Atlas dashboard.

## After Getting the Connection String

Update your `.env` file:
```env
MONGODB_URI=<your-standard-connection-string-here>
MONGODB_NAME=aircraft_tickets
```

Then run:
```bash
python -m uvicorn main:app --reload