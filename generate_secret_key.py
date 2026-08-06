"""
Generate a secure SECRET_KEY for Django
Run this script to generate a new secret key for your .env file
"""

from django.core.management.utils import get_random_secret_key

if __name__ == "__main__":
    secret_key = get_random_secret_key()
    print("\n" + "=" * 70)
    print("Django SECRET_KEY Generated Successfully!")
    print("=" * 70)
    print("\nCopy the following line to your .env file:\n")
    print(f"SECRET_KEY={secret_key}")
    print("\n" + "=" * 70)
    print("\nIMPORTANT: Keep this key secret and never commit it to version control!")
    print("=" * 70 + "\n")

