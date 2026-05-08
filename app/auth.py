"""Flask-Login user class for admin authentication."""
import bcrypt
from flask_login import UserMixin
from .models import get_admin_by_email, get_db


class AdminUser(UserMixin):
    def __init__(self, user_data: dict):
        self.id = user_data["id"]
        self.email = user_data["email"]
        self.password_hash = user_data["password_hash"]

    @staticmethod
    def get(user_id: str) -> "AdminUser | None":
        db = get_db()
        result = db.table("admin_users").select("*").eq("id", user_id).limit(1).execute()
        if result.data:
            return AdminUser(result.data[0])
        return None

    @staticmethod
    def authenticate(email: str, password: str) -> "AdminUser | None":
        user_data = get_admin_by_email(email)
        if not user_data:
            return None
        if bcrypt.checkpw(password.encode(), user_data["password_hash"].encode()):
            return AdminUser(user_data)
        return None

    @staticmethod
    def create(email: str, password: str) -> "AdminUser":
        from .models import create_admin_user
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user_data = create_admin_user(email, password_hash)
        return AdminUser(user_data)
