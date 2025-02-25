from datetime import datetime
from flask_login import UserMixin
from app import db, bcrypt, login_manager

class Role:
    USER = 'user'
    APPROVER = 'approver'
    ADMIN = 'admin'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default=Role.USER)
    line_user_id = db.Column(db.String(50), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    room_bookings = db.relationship('RoomBooking', backref='user', lazy=True)
    vehicle_bookings = db.relationship('VehicleBooking', backref='user', lazy=True)
    
    def __init__(self, username, email, password, role=Role.USER):
        self.username = username
        self.email = email
        self.password = password
        self.role = role
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == Role.ADMIN
    
    def is_approver(self):
        return self.role == Role.APPROVER
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
