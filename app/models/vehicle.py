from datetime import datetime
from app import db
from app.models.room import BookingStatus

class VehicleType:
    CAR = 'car'
    VAN = 'van'
    BUS = 'bus'
    TRUCK = 'truck'

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    vehicle_type = db.Column(db.String(20), nullable=False)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('VehicleBooking', backref='vehicle', lazy=True)
    
    def __repr__(self):
        return f'<Vehicle {self.name} ({self.plate_number})>'

class VehicleBooking(db.Model):
    __tablename__ = 'vehicle_bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    passengers = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.Text)
    status = db.Column(db.String(20), default=BookingStatus.PENDING)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VehicleBooking {self.title}>'
