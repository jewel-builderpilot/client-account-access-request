"""
One-time script to create the first admin user.
Usage: python scripts/create_admin.py <email> <password>
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.auth import AdminUser


def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/create_admin.py <email> <password>")
        sys.exit(1)

    email, password = sys.argv[1], sys.argv[2]
    app = create_app("development")

    with app.app_context():
        user = AdminUser.create(email, password)
        print(f"Admin created: {user.email} (id: {user.id})")


if __name__ == "__main__":
    main()
