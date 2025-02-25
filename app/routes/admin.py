from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from app.models import User, Room, Vehicle, RoomBooking, VehicleBooking, Role, BookingStatus
from app import db
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Get statistics
    total_users = User.query.count()
    total_rooms = Room.query.count()
    total_vehicles = Vehicle.query.count()
    pending_bookings = (
        RoomBooking.query.filter_by(status=BookingStatus.PENDING).count() +
        VehicleBooking.query.filter_by(status=BookingStatus.PENDING).count()
    )
    
    # Get recent bookings
    room_bookings = RoomBooking.query.order_by(RoomBooking.created_at.desc()).limit(5).all()
    vehicle_bookings = VehicleBooking.query.order_by(VehicleBooking.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
        total_users=total_users,
        total_rooms=total_rooms,
        total_vehicles=total_vehicles,
        pending_bookings=pending_bookings,
        room_bookings=room_bookings,
        vehicle_bookings=vehicle_bookings
    )

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            password=request.form['password'],
            role=request.form['role']
        )
        db.session.add(user)
        db.session.commit()
        flash('เพิ่มผู้ใช้สำเร็จ', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html')

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        if request.form.get('password'):
            user.password = request.form['password']
        user.role = request.form['role']
        db.session.commit()
        flash('แก้ไขผู้ใช้สำเร็จ', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', user=user)

@admin_bp.route('/rooms/manage')
@login_required
@admin_required
def manage_rooms():
    rooms = Room.query.all()
    return render_template('admin/rooms.html', rooms=rooms)

@admin_bp.route('/rooms/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_room():
    if request.method == 'POST':
        room = Room(
            name=request.form['name'],
            capacity=int(request.form['capacity']),
            description=request.form['description'],
            facilities=json.dumps(request.form.getlist('facilities'))
        )
        db.session.add(room)
        db.session.commit()
        flash('เพิ่มห้องประชุมสำเร็จ', 'success')
        return redirect(url_for('admin.manage_rooms'))
    return render_template('admin/room_form.html')

@admin_bp.route('/vehicles/manage')
@login_required
@admin_required
def manage_vehicles():
    vehicles = Vehicle.query.all()
    return render_template('admin/vehicles.html', vehicles=vehicles)

@admin_bp.route('/vehicles/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_vehicle():
    if request.method == 'POST':
        vehicle = Vehicle(
            name=request.form['name'],
            vehicle_type=request.form['vehicle_type'],
            plate_number=request.form['plate_number'],
            capacity=int(request.form['capacity']),
            description=request.form['description']
        )
        db.session.add(vehicle)
        db.session.commit()
        flash('เพิ่มยานพาหนะสำเร็จ', 'success')
        return redirect(url_for('admin.manage_vehicles'))
    return render_template('admin/vehicle_form.html')

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    return render_template('admin/reports.html')

@admin_bp.route('/reports/export', methods=['POST'])
@login_required
@admin_required
def export_report():
    report_type = request.form['type']
    start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d') + timedelta(days=1)
    
    if report_type == 'rooms':
        bookings = RoomBooking.query.filter(
            RoomBooking.created_at.between(start_date, end_date)
        ).all()
        
        data = []
        for booking in bookings:
            data.append({
                'ID': booking.id,
                'ห้องประชุม': booking.room.name,
                'ผู้จอง': booking.user.username,
                'หัวข้อ': booking.title,
                'เริ่ม': booking.start_time,
                'สิ้นสุด': booking.end_time,
                'จำนวนผู้เข้าร่วม': booking.attendees,
                'สถานะ': booking.status,
                'วันที่สร้าง': booking.created_at
            })
    else:
        bookings = VehicleBooking.query.filter(
            VehicleBooking.created_at.between(start_date, end_date)
        ).all()
        
        data = []
        for booking in bookings:
            data.append({
                'ID': booking.id,
                'ยานพาหนะ': booking.vehicle.name,
                'ผู้จอง': booking.user.username,
                'หัวข้อ': booking.title,
                'เริ่ม': booking.start_time,
                'สิ้นสุด': booking.end_time,
                'ปลายทาง': booking.destination,
                'จำนวนผู้โดยสาร': booking.passengers,
                'สถานะ': booking.status,
                'วันที่สร้าง': booking.created_at
            })
    
    df = pd.DataFrame(data)
    
    # Create Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'report_{report_type}_{start_date.strftime("%Y%m%d")}.xlsx'
    )
