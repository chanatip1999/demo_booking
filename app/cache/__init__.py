from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 300
})

def init_cache(app):
    cache.init_app(app)

# Decorators สำหรับ cache
def cache_vehicle(timeout=300):
    """Cache สำหรับข้อมูลยานพาหนะ"""
    return cache.memoize(timeout=timeout)

def cache_room(timeout=300):
    """Cache สำหรับข้อมูลห้องประชุม"""
    return cache.memoize(timeout=timeout)

def invalidate_vehicle_cache(vehicle_id):
    """ล้าง cache ของยานพาหนะ"""
    cache.delete_memoized('get_vehicle', vehicle_id)

def invalidate_room_cache(room_id):
    """ล้าง cache ของห้องประชุม"""
    cache.delete_memoized('get_room', room_id)
