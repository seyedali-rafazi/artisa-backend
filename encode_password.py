"""Helper script to URL-encode MongoDB password."""

from urllib.parse import quote_plus

# Your MongoDB password
password = "25%jA+x*fJes6Zu"

# Encode it
encoded = quote_plus(password)

print("Original password:", password)
print("Encoded password:", encoded)
print("\nUse this in your .env file:")
print(f"MONGODB_URI=mongodb+srv://rfzali93:{encoded}@cluster0.bnltfut.mongodb.net/")

# Made with Bob
