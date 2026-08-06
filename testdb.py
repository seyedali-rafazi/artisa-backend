from pymongo import MongoClient

uri = "mongodb+srv://rfzali93:25%25jA%2Bx%2AfJes6Zu@cluster0.bnltfut.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(uri)

    # تست اتصال
    client.admin.command("ping")

    print("✅ Connected to MongoDB Atlas")

except Exception as e:
    print("❌ Connection failed")
    print(e)