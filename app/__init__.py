import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_talisman import Talisman
from .config import config

csrf = CSRFProtect()
login_manager = LoginManager()


def create_app(config_name: str | None = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config[config_name])

    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "admin.login"
    login_manager.login_message = "Please log in to access the admin panel."
    login_manager.login_message_category = "warning"

    force_https = app.config.get("TALISMAN_FORCE_HTTPS", True)
    csp = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'", "cdn.tailwindcss.com"],
        "style-src": ["'self'", "'unsafe-inline'", "cdn.tailwindcss.com", "fonts.googleapis.com"],
        "font-src": ["'self'", "fonts.gstatic.com"],
        "img-src": ["'self'", "data:"],
    }
    Talisman(app, force_https=force_https, content_security_policy=csp)

    from .routes.client import client_bp
    from .routes.admin import admin_bp

    app.register_blueprint(client_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @login_manager.user_loader
    def load_user(user_id):
        from .auth import AdminUser
        return AdminUser.get(user_id)

    return app
