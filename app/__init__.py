from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from celery import Celery
from config import config
import redis

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()
celery = Celery()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    
    # Setup login view
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Initialize Celery
    celery.conf.update(app.config)
    
    # Initialize Redis
    app.redis = redis.from_url(app.config['REDIS_URL'])
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.rooms import rooms_bp
    from app.routes.vehicles import vehicles_bp
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp
    from app.routes.line_webhook import line_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(line_bp)
    
    return app
