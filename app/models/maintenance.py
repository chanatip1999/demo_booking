from datetime import datetime
from . import db

class Maintenance(db.Model):
    """โมเดลสำหรับการบำรุงรักษา"""
    __tablename__ = 'maintenances'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    type = db.Column(db.String(50), nullable=False)  # ประเภทการบำรุงรักษา
    description = db.Column(db.Text)
    cost = db.Column(db.Float)  # ค่าใช้จ่าย
    performed_by = db.Column(db.String(100))  # ผู้ดำเนินการ
    next_maintenance_date = db.Column(db.DateTime)  # วันที่ต้องบำรุงรักษาครั้งถัดไป
    status = db.Column(db.String(20), default='pending')  # สถานะ: pending, completed, cancelled
    
    # ความสัมพันธ์กับตารางอื่น
    vehicle = db.relationship('Vehicle', backref=db.backref('maintenances', lazy=True))
    
    def __repr__(self):
        return f'<Maintenance {self.id}: {self.type} for Vehicle {self.vehicle_id}>'

class MaintenanceSchedule(db.Model):
    """โมเดลสำหรับกำหนดการบำรุงรักษา"""
    __tablename__ = 'maintenance_schedules'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    maintenance_type = db.Column(db.String(50), nullable=False)
    interval_days = db.Column(db.Integer, nullable=False)  # ระยะเวลาระหว่างการบำรุงรักษา (วัน)
    last_maintenance = db.Column(db.DateTime)
    next_maintenance = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # ความสัมพันธ์กับตารางอื่น
    vehicle = db.relationship('Vehicle', backref=db.backref('maintenance_schedules', lazy=True))

    def __repr__(self):
        return f'<MaintenanceSchedule {self.id}: {self.maintenance_type} for Vehicle {self.vehicle_id}>'
