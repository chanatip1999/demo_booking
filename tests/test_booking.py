import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Room, Vehicle, RoomBooking, VehicleBooking

@pytest.fixture
def app():
    """สร้าง app สำหรับการทดสอบ"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(app, client):
    """สร้าง headers สำหรับ authentication"""
    # สร้างผู้ใช้สำหรับทดสอบ
    user = User(
        email='test@example.com',
        name='Test User',
        password='password123'
    )
    with app.app_context():
        db.session.add(user)
        db.session.commit()
        
    # Login
    response = client.post('/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    token = response.json['token']
    
    return {'Authorization': f'Bearer {token}'}

def test_room_booking(client, auth_headers):
    """ทดสอบการจองห้องประชุม"""
    # สร้างห้องประชุมสำหรับทดสอบ
    room = Room(
        name='Test Room',
        capacity=10,
        location='Floor 1'
    )
    with app.app_context():
        db.session.add(room)
        db.session.commit()
        
    # ทดสอบการจองห้อง
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=2)
    
    response = client.post('/api/rooms/book', json={
        'room_id': room.id,
        'title': 'Test Meeting',
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'attendees': 5
    }, headers=auth_headers)
    
    assert response.status_code == 201
    assert response.json['status'] == 'pending'

def test_vehicle_booking(client, auth_headers):
    """ทดสอบการจองยานพาหนะ"""
    # สร้างยานพาหนะสำหรับทดสอบ
    vehicle = Vehicle(
        name='Test Vehicle',
        vehicle_type='Car',
        capacity=4,
        plate_number='TEST123'
    )
    with app.app_context():
        db.session.add(vehicle)
        db.session.commit()
        
    # ทดสอบการจองยานพาหนะ
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=4)
    
    response = client.post('/api/vehicles/book', json={
        'vehicle_id': vehicle.id,
        'title': 'Test Trip',
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'destination': 'Test Location',
        'passengers': 3
    }, headers=auth_headers)
    
    assert response.status_code == 201
    assert response.json['status'] == 'pending'

def test_booking_conflict(client, auth_headers):
    """ทดสอบการจองที่ทับซ้อนกัน"""
    # สร้างห้องประชุมและการจองที่มีอยู่แล้ว
    room = Room(name='Test Room', capacity=10)
    existing_booking = RoomBooking(
        room_id=room.id,
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=2),
        title='Existing Meeting'
    )
    
    with app.app_context():
        db.session.add(room)
        db.session.add(existing_booking)
        db.session.commit()
        
    # พยายามจองในเวลาที่ทับซ้อน
    response = client.post('/api/rooms/book', json={
        'room_id': room.id,
        'title': 'Conflicting Meeting',
        'start_time': existing_booking.start_time.isoformat(),
        'end_time': existing_booking.end_time.isoformat(),
        'attendees': 5
    }, headers=auth_headers)
    
    assert response.status_code == 409
    assert 'conflict' in response.json['error'].lower()

def test_booking_approval(client, auth_headers):
    """ทดสอบการอนุมัติการจอง"""
    # สร้างผู้ใช้ที่เป็น approver
    approver = User(
        email='approver@example.com',
        name='Approver',
        password='password123',
        role='approver'
    )
    
    # สร้างการจองที่รอการอนุมัติ
    room = Room(name='Test Room', capacity=10)
    booking = RoomBooking(
        room_id=room.id,
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=2),
        title='Pending Meeting',
        status='pending'
    )
    
    with app.app_context():
        db.session.add(approver)
        db.session.add(room)
        db.session.add(booking)
        db.session.commit()
        
    # Login as approver
    response = client.post('/auth/login', json={
        'email': 'approver@example.com',
        'password': 'password123'
    })
    approver_headers = {'Authorization': f'Bearer {response.json["token"]}'}
    
    # ทดสอบการอนุมัติ
    response = client.post(f'/api/bookings/{booking.id}/approve',
        headers=approver_headers)
    
    assert response.status_code == 200
    assert response.json['status'] == 'approved'
