from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Room, RoomBooking, BookingStatus, User
from app import db
from app.tasks.notifications import send_booking_request_notification, send_booking_status_notification
from datetime import datetime
import json

rooms_bp = Blueprint('rooms', __name__)

@rooms_bp.route('/rooms')
@login_required
def list_rooms():
    rooms = Room.query.filter_by(is_active=True).all()
    return render_template('rooms/list.html', rooms=rooms)

@rooms_bp.route('/rooms/<int:room_id>')
@login_required
def room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    return render_template('rooms/detail.html', room=room)

@rooms_bp.route('/rooms/book/<int:room_id>', methods=['GET', 'POST'])
@login_required
def book_room(room_id):
    room = Room.query.get_or_404(room_id)
    
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
        conflict = RoomBooking.query.filter(
            RoomBooking.room_id == room_id,
            RoomBooking.status != BookingStatus.REJECTED,
            RoomBooking.start_time < end_time,
            RoomBooking.end_time > start_time
        ).first()
        
        if conflict:
            flash('ห้องประชุมถูกจองในช่วงเวลาดังกล่าวแล้ว', 'danger')
            return redirect(url_for('rooms.book_room', room_id=room_id))
        
        booking = RoomBooking(
            room_id=room_id,
            user_id=current_user.id,
            title=request.form['title'],
            start_time=start_time,
            end_time=end_time,
            attendees=int(request.form['attendees']),
            purpose=request.form['purpose']
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Send notification to approvers
        send_booking_request_notification.delay('room', booking.id)
        
        flash('คำขอจองห้องประชุมถูกส่งไปยังผู้อนุมัติแล้ว', 'success')
        return redirect(url_for('rooms.my_bookings'))
    
    return render_template('rooms/book.html', room=room)

@rooms_bp.route('/rooms/bookings')
@login_required
def my_bookings():
    bookings = RoomBooking.query.filter_by(user_id=current_user.id)\
        .order_by(RoomBooking.created_at.desc()).all()
    return render_template('rooms/my_bookings.html', bookings=bookings)

@rooms_bp.route('/rooms/approve')
@login_required
def approve_list():
    if not current_user.is_approver() and not current_user.is_admin():
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'danger')
        return redirect(url_for('main.index'))
    
    bookings = RoomBooking.query.filter_by(status=BookingStatus.PENDING)\
        .order_by(RoomBooking.created_at.desc()).all()
    return render_template('rooms/approve_list.html', bookings=bookings)

@rooms_bp.route('/rooms/bookings/<int:booking_id>/<action>')
@login_required
def booking_action(booking_id, action):
    if not current_user.is_approver() and not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    booking = RoomBooking.query.get_or_404(booking_id)
    
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
    send_booking_status_notification.delay('room', booking.id, booking.status)
    
    return redirect(url_for('rooms.approve_list'))
