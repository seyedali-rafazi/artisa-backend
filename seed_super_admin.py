"""Bootstrap script to create or promote the initial Super Admin account."""

import asyncio
import sys
from passlib.context import CryptContext

from core.database import db
from models.user import User, RoleEnum

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_super_admin(name: str = "مدیر ارشد سیستم", email: str = "superadmin@artisa.com", password: str = "SuperAdmin@123456"):
    """Create or update initial Super Admin."""
    print("Connecting to MongoDB...")
    await db.connect_db()

    user = await User.find_one(User.email == email)
    hashed_pwd = pwd_context.hash(password)

    if user:
        print(f"User {email} exists. Promoting to Super Admin...")
        user.role = RoleEnum.SUPER_ADMIN.value
        user.is_superuser = True
        user.is_active = True
        user.is_verified = True
        user.email_verified = True
        user.hashed_password = hashed_pwd
        await user.save()
        print(f"User {email} is now Super Admin.")
    else:
        print(f"Creating Super Admin user: {email}...")
        new_user = User(
            name=name,
            email=email,
            hashed_password=hashed_pwd,
            role=RoleEnum.SUPER_ADMIN.value,
            is_superuser=True,
            is_active=True,
            is_verified=True,
            email_verified=True,
            provider="local",
        )
        await new_user.insert()
        print(f"Super Admin user created: {email} / Password: {password}")

    await db.close_db()

if __name__ == "__main__":
    email_arg = sys.argv[1] if len(sys.argv) > 1 else "superadmin@artisa.com"
    pass_arg = sys.argv[2] if len(sys.argv) > 2 else "SuperAdmin@123456"
    asyncio.run(seed_super_admin(email=email_arg, password=pass_arg))
