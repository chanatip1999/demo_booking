from app.routes.auth import auth_bp
from app.routes.rooms import rooms_bp
from app.routes.vehicles import vehicles_bp
from app.routes.api import api_bp
from app.routes.admin import admin_bp
from app.routes.line_webhook import line_bp

__all__ = [
    'auth_bp',
    'rooms_bp',
    'vehicles_bp',
    'api_bp',
    'admin_bp',
    'line_bp'
]
