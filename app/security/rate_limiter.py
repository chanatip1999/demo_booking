from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Custom decorators for specific rate limits
login_limit = limiter.limit(
    "5 per minute",
    error_message="มีการพยายามเข้าสู่ระบบมากเกินไป กรุณารอสักครู่"
)

api_limit = limiter.limit(
    "1000 per hour",
    error_message="เกินขีดจำกัดการเรียก API กรุณารอสักครู่"
)
