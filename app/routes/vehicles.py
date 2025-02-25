from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Vehicle, VehicleBooking, BookingStatus, User
from app import db
from app.tasks.notifications import send_booking_request_notification, send_booking_status_notification
from datetime import datetime

vehicles_bp = Blueprint('vehicles', __name__)

@vehicles_bp.route('/vehicles')
@login_required
def list_vehicles():
    vehicles = Vehicle.query.filter_by(is_active=True).all()
    return render_template('vehicles/list.html', vehicles=vehicles)

@vehicles_bp.route('/vehicles/<int:vehicle_id>')
@login_required
def vehicle_detail(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    return render_template('vehicles/detail.html', vehicle=vehicle)

@vehicles_bp.route('/vehicles/book/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def book_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    if request.method == 'POST':
        start_time = datetime.strptime(
            f"{request.form['date']} {request.form['start_time']}",
            '%Y-%m-%d %H:%M'
        )
        end_time = datetime.strptime(
            f"{request.form['date']} {request.form['end_time']}",
            '%Y-%m-%d %H:%M'
        )
        
        # Check for booking conflicts
        conflict = VehicleBooking.query.filter(
            VehicleBooking.vehicle_id == vehicle_id,
            VehicleBooking.status != BookingStatus.REJECTED,
            VehicleBooking.start_time < end_time,
            VehicleBooking.end_time > start_time
        ).first()
        
        if conflict:
            flash('ยานพาหนะถูกจองในช่วงเวลาดังกล่าวแล้ว', 'danger')
            return redirect(url_for('vehicles.book_vehicle', vehicle_id=vehicle_id))
        
        booking = VehicleBooking(
            vehicle_id=vehicle_id,
            user_id=current_user.id,
            title=request.form['title'],
            start_time=start_time,
            end_time=end_time,
            destination=request.form['destination'],
            passengers=int(request.form['passengers']),
            purpose=request.form['purpose']
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Send notification to approvers
        send_booking_request_notification.delay('vehicle', booking.id)
        
        flash('คำขอจองยานพาหนะถูกส่งไปยังผู้อนุมัติแล้ว', 'success')
        return redirect(url_for('vehicles.my_bookings'))
    
    return render_template('vehicles/book.html', vehicle=vehicle)

@vehicles_bp.route('/vehicles/bookings')
@login_required
def my_bookings():
    bookings = VehicleBooking.query.filter_by(user_id=current_user.id)\
        .order_by(VehicleBooking.created_at.desc()).all()
    return render_template('vehicles/my_bookings.html', bookings=bookings)

@vehicles_bp.route('/vehicles/approve')
@login_required
def approve_list():
    if not current_user.is_approver() and not current_user.is_admin():
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'danger')
        return redirect(url_for('main.index'))
    
    bookings = VehicleBooking.query.filter_by(status=BookingStatus.PENDING)\
        .order_by(VehicleBooking.created_at.desc()).all()
    return render_template('vehicles/approve_list.html', bookings=bookings)

@vehicles_bp.route('/vehicles/bookings/<int:booking_id>/<action>')
@login_required
def booking_action(booking_id, action):
    if not current_user.is_approver() and not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    booking = VehicleBooking.query.get_or_404(booking_id)
    
    if action == 'approve':
        booking.status = BookingStatus.APPROVED
        booking.approved_by = current_user.id
        booking.approved_at = datetime.utcnow()
        flash('อนุมัติการจองเรียบร้อยแล้ว', 'success')
    elif action == 'reject':
        booking.status = BookingStatus.REJECTED
        booking.approved_by = current_user.id
        booking.approved_at = datetime.utcnow()
        flash('ปฏิเสธการจองเรียบร้อยแล้ว', 'warning')
    else:
        return jsonify({'error': 'Invalid action'}), 400
    
    db.session.commit()
    
    # Send notification to user
    send_booking_status_notification.delay('vehicle', booking.id, booking.status)
    
    return redirect(url_for('vehicles.approve_list'))
