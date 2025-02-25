from datetime import datetime
from flask import current_app
from ..models import db

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

def log_audit(user_id, action, resource_type, resource_id, details=None, ip_address=None):
    """บันทึก audit log"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address
    )
    db.session.add(log)
    db.session.commit()

# Decorator สำหรับบันทึก audit log
def audit_log(action, resource_type):
    def decorator(f):
        def wrapped(*args, **kwargs):
            result = f(*args, **kwargs)
            # บันทึก log หลังจากฟังก์ชันทำงานเสร็จ
            log_audit(
                user_id=current_user.id if current_user else None,
                action=action,
                resource_type=resource_type,
                resource_id=kwargs.get('id'),
                ip_address=request.remote_addr
            )
            return result
        return wrapped
    return decorator
