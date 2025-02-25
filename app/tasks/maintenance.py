from celery import shared_task
from datetime import datetime, timedelta
from ..models import Vehicle, Maintenance, User
from ..notifications import send_line_notification

@shared_task
def check_vehicle_maintenance():
    """ตรวจสอบการบำรุงรักษายานพาหนะ"""
    vehicles = Vehicle.query.all()
    for vehicle in vehicles:
        # ตรวจสอบการบำรุงรักษาครั้งล่าสุด
        last_maintenance = Maintenance.query.filter_by(
            vehicle_id=vehicle.id
        ).order_by(Maintenance.date.desc()).first()
        
        if last_maintenance:
            next_maintenance = last_maintenance.date + timedelta(days=90)  # ทุก 3 เดือน
            if next_maintenance <= datetime.now():
                # แจ้งเตือนผู้ดูแลระบบ
                admins = User.query.filter_by(role='admin').all()
                for admin in admins:
                    send_line_notification(
                        admin.line_user_id,
                        f"แจ้งเตือน: ถึงเวลาบำรุงรักษายานพาหนะ {vehicle.name} "
                        f"(ทะเบียน: {vehicle.plate_number})"
                    )

@shared_task
def calculate_maintenance_costs():
    """คำนวณค่าใช้จ่ายในการบำรุงรักษา"""
    vehicles = Vehicle.query.all()
    report = []
    
    for vehicle in vehicles:
        maintenances = Maintenance.query.filter_by(
            vehicle_id=vehicle.id,
            date__gte=datetime.now() - timedelta(days=365)  # ข้อมูล 1 ปีย้อนหลัง
        ).all()
        
        total_cost = sum(m.cost for m in maintenances)
        report.append({
            'vehicle': vehicle.name,
            'plate_number': vehicle.plate_number,
            'maintenance_count': len(maintenances),
            'total_cost': total_cost
        })
    
    return report
