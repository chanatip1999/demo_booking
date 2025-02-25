from flask import Blueprint, request, abort
from app.models import User, RoomBooking, VehicleBooking, BookingStatus
from app.services.line_service import LineService
from app import db
from linebot.exceptions import InvalidSignatureError
from datetime import datetime
import json

line_bp = Blueprint('line', __name__)

@line_bp.route("/webhook", methods=['POST'])
def webhook():
    line_service = LineService()
    signature = request.headers.get('X-Line-Signature')
    
    if not signature:
        abort(400)
        
    body = request.get_data(as_text=True)
    
    try:
        line_service.handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
        
    return 'OK'

@line_bp.route("/link-line/<token>", methods=['GET'])
def link_line_account(token):
    """Link LINE account with user account"""
    # This endpoint should be called from LINE login
    # Implementation depends on how you handle LINE login
    pass

@line_service.handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """Handle text messages from LINE"""
    user = User.query.filter_by(line_user_id=event.source.user_id).first()
    if not user:
        line_service.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="กรุณาเชื่อมต่อบัญชี LINE กับระบบก่อนใช้งาน")
        )
        return
        
    # Handle user commands
    text = event.message.text.lower()
    if text == 'bookings':
        show_user_bookings(event, user)
    else:
        line_service.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ไม่เข้าใจคำสั่ง กรุณาลองใหม่อีกครั้ง")
        )

@line_service.handler.add(PostbackEvent)
def handle_postback(event):
    """Handle postback actions from LINE"""
    user = User.query.filter_by(line_user_id=event.source.user_id).first()
    if not user or not (user.is_approver() or user.is_admin()):
        line_service.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="คุณไม่มีสิทธิ์ดำเนินการนี้")
        )
        return
        
    data = dict(parse_qs(event.postback.data))
    action = data.get('action', [None])[0]
    booking_type = data.get('type', [None])[0]
    booking_id = int(data.get('id', [0])[0])
    
    if not all([action, booking_type, booking_id]):
        line_service.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ข้อมูลไม่ถูกต้อง")
        )
        return
        
    # Get booking
    if booking_type == 'room':
        booking = RoomBooking.query.get(booking_id)
    else:
        booking = VehicleBooking.query.get(booking_id)
        
    if not booking:
        line_service.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ไม่พบรายการจอง")
        )
        return
        
    # Update booking status
    if action == 'approve':
        booking.status = BookingStatus.APPROVED
        message = "อนุมัติการจองเรียบร้อยแล้ว"
    else:
        booking.status = BookingStatus.REJECTED
        message = "ปฏิเสธการจองเรียบร้อยแล้ว"
        
    booking.approved_by = user.id
    booking.approved_at = datetime.utcnow()
    db.session.commit()
    
    # Send notification to user
    if booking.user.line_user_id:
        line_service.send_booking_status(
            booking.user.line_user_id,
            booking_type,
            booking,
            booking.status
        )
    
    line_service.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message)
    )

def show_user_bookings(event, user):
    """Show user's bookings in LINE message"""
    room_bookings = RoomBooking.query.filter_by(user_id=user.id)\
        .order_by(RoomBooking.created_at.desc()).limit(5).all()
        
    vehicle_bookings = VehicleBooking.query.filter_by(user_id=user.id)\
        .order_by(VehicleBooking.created_at.desc()).limit(5).all()
        
    message = "รายการจองล่าสุดของคุณ:\n\n"
    
    if room_bookings:
        message += "🏢 ห้องประชุม:\n"
        for booking in room_bookings:
            message += (
                f"- {booking.room.name}\n"
                f"  หัวข้อ: {booking.title}\n"
                f"  วันที่: {booking.start_time.strftime('%Y-%m-%d %H:%M')}\n"
                f"  สถานะ: {booking.status}\n\n"
            )
            
    if vehicle_bookings:
        message += "🚗 ยานพาหนะ:\n"
        for booking in vehicle_bookings:
            message += (
                f"- {booking.vehicle.name}\n"
                f"  หัวข้อ: {booking.title}\n"
                f"  วันที่: {booking.start_time.strftime('%Y-%m-%d %H:%M')}\n"
                f"  สถานะ: {booking.status}\n\n"
            )
            
    if not room_bookings and not vehicle_bookings:
        message = "คุณยังไม่มีรายการจอง"
        
    line_service.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message)
    )
