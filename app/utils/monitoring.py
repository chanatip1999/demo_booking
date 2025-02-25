from prometheus_flask_exporter import PrometheusMetrics
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from functools import wraps
from flask import request, current_app
import time

# Prometheus metrics
metrics = PrometheusMetrics(app=None)

# Custom metrics
request_latency = metrics.histogram(
    'request_latency_seconds',
    'Request latency in seconds',
    ['endpoint']
)

booking_counter = metrics.counter(
    'booking_total',
    'Total number of bookings',
    ['type', 'status']
)

def init_monitoring(app):
    """ตั้งค่าระบบ monitoring"""
    # Initialize Prometheus metrics
    metrics.init_app(app)
    
    # Initialize Sentry
    sentry_sdk.init(
        dsn=app.config.get('SENTRY_DSN'),
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0
    )

def monitor_endpoint(f):
    """Decorator สำหรับเก็บ metrics ของ endpoint"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            response = f(*args, **kwargs)
            # บันทึกเวลาที่ใช้
            request_latency.labels(
                endpoint=request.endpoint
            ).observe(time.time() - start_time)
            return response
            
        except Exception as e:
            # ส่ง error ไปยัง Sentry
            sentry_sdk.capture_exception(e)
            raise
            
    return decorated_function

def log_booking(booking_type, status):
    """บันทึกสถิติการจอง"""
    booking_counter.labels(
        type=booking_type,
        status=status
    ).inc()

def setup_custom_monitoring():
    """ตั้งค่า custom monitoring metrics"""
    # Database connection monitoring
    @metrics.gauge('db_connection_pool_size', 'Database connection pool size')
    def get_db_pool_size():
        return current_app.db.engine.pool.size()
    
    # Cache hit ratio monitoring
    @metrics.gauge('cache_hit_ratio', 'Cache hit ratio')
    def get_cache_hit_ratio():
        stats = current_app.cache.get_stats()
        hits = stats.get('hits', 0)
        misses = stats.get('misses', 0)
        total = hits + misses
        return (hits / total) if total > 0 else 0
    
    # System health check
    @metrics.gauge('system_health', 'System health status')
    def check_system_health():
        # ตรวจสอบการเชื่อมต่อกับ dependencies ต่างๆ
        try:
            # ตรวจสอบ database
            current_app.db.session.execute('SELECT 1')
            # ตรวจสอบ cache
            current_app.cache.get('health_check')
            # ตรวจสอบ LINE API
            # TODO: implement LINE API health check
            return 1  # healthy
        except:
            return 0  # unhealthy
