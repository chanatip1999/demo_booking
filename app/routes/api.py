from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import Room, Vehicle, RoomBooking, VehicleBooking, BookingStatus
from app import db
from datetime import datetime
from functools import wraps

api_bp = Blueprint('api', __name__)

def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def approver_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Unauthorized'}), 401
        if not (current_user.is_approver() or current_user.is_admin()):
            return jsonify({'error': 'Forbidden'}), 403
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/rooms')
@api_login_required
def list_rooms():
    rooms = Room.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': room.id,
        'name': room.name,
        'capacity': room.capacity,
        'description': room.description,
        'facilities': room.facilities
    } for room in rooms])

@api_bp.route('/rooms/<int:room_id>')
@api_login_required
def get_room(room_id):
    room = Room.query.get_or_404(room_id)
    return jsonify({
        'id': room.id,
        'name': room.name,
        'capacity': room.capacity,
        'description': room.description,
        'facilities': room.facilities
    })

@api_bp.route('/rooms/book', methods=['POST'])
@api_login_required
def book_room():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['room_id', 'title', 'start_time', 'end_time', 'attendees']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
        
    # Parse dates
    try:
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
        
    # Check room exists
    room = Room.query.get(data['room_id'])
    if not room:
        return jsonify({'error': 'Room not found'}), 404
        
    # Check for conflicts
    conflict = RoomBooking.query.filter(
        RoomBooking.room_id == data['room_id'],
        RoomBooking.status != BookingStatus.REJECTED,
        RoomBooking.start_time < end_time,
        RoomBooking.end_time > start_time
    ).first()
    
    if conflict:
        return jsonify({'error': 'Room already booked for this time'}), 409
        
    # Create booking
    booking = RoomBooking(
        room_id=data['room_id'],
        user_id=current_user.id,
        title=data['title'],
        start_time=start_time,
        end_time=end_time,
        attendees=data['attendees'],
        purpose=data.get('purpose', '')
    )
    
    db.session.add(booking)
    db.session.commit()
    
    return jsonify({
        'id': booking.id,
        'status': booking.status,
        'message': 'Booking request sent successfully'
    })

@api_bp.route('/vehicles')
@api_login_required
def list_vehicles():
    vehicles = Vehicle.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': vehicle.id,
        'name': vehicle.name,
        'type': vehicle.vehicle_type,
        'capacity': vehicle.capacity,
        'description': vehicle.description
    } for vehicle in vehicles])

@api_bp.route('/vehicles/<int:vehicle_id>')
@api_login_required
def get_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    return jsonify({
        'id': vehicle.id,
        'name': vehicle.name,
        'type': vehicle.vehicle_type,
        'capacity': vehicle.capacity,
        'description': vehicle.description
    })

@api_bp.route('/vehicles/book', methods=['POST'])
@api_login_required
def book_vehicle():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['vehicle_id', 'title', 'start_time', 'end_time', 
                      'destination', 'passengers']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
        
    # Parse dates
    try:
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
        
    # Check vehicle exists
    vehicle = Vehicle.query.get(data['vehicle_id'])
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404
        
    # Check for conflicts
    conflict = VehicleBooking.query.filter(
        VehicleBooking.vehicle_id == data['vehicle_id'],
        VehicleBooking.status != BookingStatus.REJECTED,
        VehicleBooking.start_time < end_time,
        VehicleBooking.end_time > start_time
    ).first()
    
    if conflict:
        return jsonify({'error': 'Vehicle already booked for this time'}), 409
        
    # Create booking
    booking = VehicleBooking(
        vehicle_id=data['vehicle_id'],
        user_id=current_user.id,
        title=data['title'],
        start_time=start_time,
        end_time=end_time,
        destination=data['destination'],
        passengers=data['passengers'],
        purpose=data.get('purpose', '')
    )
    
    db.session.add(booking)
    db.session.commit()
    
    return jsonify({
        'id': booking.id,
        'status': booking.status,
        'message': 'Booking request sent successfully'
    })

@api_bp.route('/bookings/room/<int:booking_id>/<action>', methods=['PUT'])
@approver_required
def room_booking_action(booking_id, action):
    if action not in ['approve', 'reject']:
        return jsonify({'error': 'Invalid action'}), 400
        
    booking = RoomBooking.query.get_or_404(booking_id)
    
    if action == 'approve':
        booking.status = BookingStatus.APPROVED
    else:
        booking.status = BookingStatus.REJECTED
        
    booking.approved_by = current_user.id
    booking.approved_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'id': booking.id,
        'status': booking.status,
        'message': f'Booking {action}ed successfully'
    })

@api_bp.route('/bookings/vehicle/<int:booking_id>/<action>', methods=['PUT'])
@approver_required
def vehicle_booking_action(booking_id, action):
    if action not in ['approve', 'reject']:
        return jsonify({'error': 'Invalid action'}), 400
        
    booking = VehicleBooking.query.get_or_404(booking_id)
    
    if action == 'approve':
        booking.status = BookingStatus.APPROVED
    else:
        booking.status = BookingStatus.REJECTED
        
    booking.approved_by = current_user.id
    booking.approved_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'id': booking.id,
        'status': booking.status,
        'message': f'Booking {action}ed successfully'
    })
