from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    TextSendMessage, TemplateSendMessage, ButtonsTemplate,
    PostbackAction, MessageAction
)
from flask import current_app

class LineService:
    def __init__(self):
        self.line_bot_api = LineBotApi(current_app.config['LINE_CHANNEL_ACCESS_TOKEN'])
        self.handler = WebhookHandler(current_app.config['LINE_CHANNEL_SECRET'])
    
    def send_notification(self, line_user_id, message):
        """Send a simple text message to a LINE user"""
        self.line_bot_api.push_message(
            line_user_id,
            TextSendMessage(text=message)
        )
    
    def send_booking_request(self, line_user_id, booking_type, booking):
        """Send a booking request notification with approve/reject buttons"""
        if booking_type not in ['room', 'vehicle']:
            raise ValueError('booking_type must be either "room" or "vehicle"')
            
        title = f"การจอง{'ห้องประชุม' if booking_type == 'room' else 'ยานพาหนะ'}"
        
        # Create booking details message
        if booking_type == 'room':
            detail = (
                f"ห้อง: {booking.room.name}\n"
                f"ผู้จอง: {booking.user.username}\n"
                f"หัวข้อ: {booking.title}\n"
                f"วันที่: {booking.start_time.strftime('%Y-%m-%d %H:%M')} - "
                f"{booking.end_time.strftime('%H:%M')}\n"
                f"จำนวนผู้เข้าร่วม: {booking.attendees} คน"
            )
        else:
            detail = (
                f"ยานพาหนะ: {booking.vehicle.name}\n"
                f"ผู้จอง: {booking.user.username}\n"
                f"หัวข้อ: {booking.title}\n"
                f"วันที่: {booking.start_time.strftime('%Y-%m-%d %H:%M')} - "
                f"{booking.end_time.strftime('%H:%M')}\n"
                f"ปลายทาง: {booking.destination}\n"
                f"จำนวนผู้โดยสาร: {booking.passengers} คน"
            )
        
        buttons_template = ButtonsTemplate(
            title=title,
            text=detail,
            actions=[
                PostbackAction(
                    label='อนุมัติ',
                    data=f'action=approve&type={booking_type}&id={booking.id}'
                ),
                PostbackAction(
                    label='ปฏิเสธ',
                    data=f'action=reject&type={booking_type}&id={booking.id}'
                )
            ]
        )
        
        self.line_bot_api.push_message(
            line_user_id,
            TemplateSendMessage(
                alt_text='คำขอการจอง',
                template=buttons_template
            )
        )
    
    def send_booking_status(self, line_user_id, booking_type, booking, status):
        """Send booking status update to user"""
        if booking_type not in ['room', 'vehicle']:
            raise ValueError('booking_type must be either "room" or "vehicle"')
            
        status_text = 'ได้รับการอนุมัติ' if status == 'approved' else 'ถูกปฏิเสธ'
        booking_text = 'ห้องประชุม' if booking_type == 'room' else 'ยานพาหนะ'
        
        message = (
            f"การจอง{booking_text}ของคุณ {status_text}\n\n"
            f"รายละเอียด:\n"
            f"หัวข้อ: {booking.title}\n"
            f"วันที่: {booking.start_time.strftime('%Y-%m-%d %H:%M')} - "
            f"{booking.end_time.strftime('%H:%M')}"
        )
        
        self.line_bot_api.push_message(
            line_user_id,
            TextSendMessage(text=message)
        )
