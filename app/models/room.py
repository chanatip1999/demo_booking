from datetime import datetime
from app import db

class BookingStatus:
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

class Room(db.Model):
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    facilities = db.Column(db.Text)  # JSON string of facilities
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('RoomBooking', backref='room', lazy=True)
    
    def __repr__(self):
        return f'<Room {self.name}>'

class RoomBooking(db.Model):
    __tablename__ = 'room_bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    attendees = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.Text)
    status = db.Column(db.String(20), default=BookingStatus.PENDING)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RoomBooking {self.title}>'
