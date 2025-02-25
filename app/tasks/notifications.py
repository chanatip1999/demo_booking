from app import celery, create_app
from app.services import LineService
from app.models import User, BookingStatus
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@celery.task
def send_booking_request_notification(booking_type, booking_id):
    """Send LINE notification to approvers about new booking request"""
    app = create_app()
    with app.app_context():
        # Get all approvers
        approvers = User.query.filter_by(role='approver').all()
        line_service = LineService()
        
        if booking_type == 'room':
            from app.models import RoomBooking
            booking = RoomBooking.query.get(booking_id)
        else:
            from app.models import VehicleBooking
            booking = VehicleBooking.query.get(booking_id)
            
        if not booking:
            logger.error(f'Booking {booking_id} not found')
            return
            
        # Send notification to each approver
        for approver in approvers:
            if approver.line_user_id:
                try:
                    line_service.send_booking_request(
                        approver.line_user_id,
                        booking_type,
                        booking
                    )
                except Exception as e:
                    logger.error(f'Failed to send LINE notification to {approver.username}: {str(e)}')

@celery.task
def send_booking_status_notification(booking_type, booking_id, status):
    """Send LINE notification to user about booking status update"""
    app = create_app()
    with app.app_context():
        if booking_type == 'room':
            from app.models import RoomBooking
            booking = RoomBooking.query.get(booking_id)
        else:
            from app.models import VehicleBooking
            booking = VehicleBooking.query.get(booking_id)
            
        if not booking:
            logger.error(f'Booking {booking_id} not found')
            return
            
        user = booking.user
        if user.line_user_id:
            try:
                line_service = LineService()
                line_service.send_booking_status(
                    user.line_user_id,
                    booking_type,
                    booking,
                    status
                )
            except Exception as e:
                logger.error(f'Failed to send LINE notification to {user.username}: {str(e)}')
