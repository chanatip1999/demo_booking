import os
from datetime import datetime
import subprocess
from flask import current_app
from crontab import CronTab

class DatabaseBackup:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.backup_dir = app.config.get('BACKUP_DIR', 'backups')
        self.db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        # สร้างโฟลเดอร์สำหรับเก็บไฟล์ backup ถ้ายังไม่มี
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def create_backup(self):
        """สร้างไฟล์ backup ของฐานข้อมูล"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(self.backup_dir, f'backup_{timestamp}.sql')
        
        # สร้าง backup command ตาม database type
        if 'mysql' in self.db_uri:
            cmd = self._mysql_backup_command(backup_file)
        elif 'postgresql' in self.db_uri:
            cmd = self._postgresql_backup_command(backup_file)
        else:
            raise ValueError('Unsupported database type')
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            return backup_file
        except subprocess.CalledProcessError as e:
            current_app.logger.error(f'Backup failed: {str(e)}')
            raise

    def restore_backup(self, backup_file):
        """กู้คืนฐานข้อมูลจากไฟล์ backup"""
        if not os.path.exists(backup_file):
            raise FileNotFoundError(f'Backup file not found: {backup_file}')
        
        # สร้าง restore command ตาม database type
        if 'mysql' in self.db_uri:
            cmd = self._mysql_restore_command(backup_file)
        elif 'postgresql' in self.db_uri:
            cmd = self._postgresql_restore_command(backup_file)
        else:
            raise ValueError('Unsupported database type')
        
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            current_app.logger.error(f'Restore failed: {str(e)}')
            raise

    def setup_automatic_backup(self, schedule='0 0 * * *'):  # Default: ทุกวันเวลาเที่ยงคืน
        """ตั้งค่า cron job สำหรับ automatic backup"""
        cron = CronTab(user=True)
        
        # ลบ job เก่าถ้ามี
        cron.remove_all(comment='database_backup')
        
        # สร้าง job ใหม่
        job = cron.new(
            command=f'python -c "from app.utils.backup import DatabaseBackup; '
            f'DatabaseBackup().create_backup()"',
            comment='database_backup'
        )
        
        job.setall(schedule)
        cron.write()

    def _mysql_backup_command(self, backup_file):
        """สร้าง command สำหรับ backup MySQL database"""
        params = self._parse_db_uri()
        return (
            f'mysqldump -h {params["host"]} -P {params["port"]} -u {params["user"]} '
            f'-p{params["password"]} {params["database"]} > {backup_file}'
        )

    def _postgresql_backup_command(self, backup_file):
        """สร้าง command สำหรับ backup PostgreSQL database"""
        params = self._parse_db_uri()
        return (
            f'PGPASSWORD={params["password"]} pg_dump -h {params["host"]} '
            f'-p {params["port"]} -U {params["user"]} -d {params["database"]} '
            f'-F c -b -v -f {backup_file}'
        )

    def _mysql_restore_command(self, backup_file):
        """สร้าง command สำหรับ restore MySQL database"""
        params = self._parse_db_uri()
        return (
            f'mysql -h {params["host"]} -P {params["port"]} -u {params["user"]} '
            f'-p{params["password"]} {params["database"]} < {backup_file}'
        )

    def _postgresql_restore_command(self, backup_file):
        """สร้าง command สำหรับ restore PostgreSQL database"""
        params = self._parse_db_uri()
        return (
            f'PGPASSWORD={params["password"]} pg_restore -h {params["host"]} '
            f'-p {params["port"]} -U {params["user"]} -d {params["database"]} '
            f'-v {backup_file}'
        )

    def _parse_db_uri(self):
        """แยกส่วนประกอบจาก database URI"""
        # ตัวอย่าง URI: mysql://user:pass@localhost:3306/dbname
        parts = self.db_uri.split('://')
        auth = parts[1].split('@')
        user_pass = auth[0].split(':')
        host_db = auth[1].split('/')
        host_port = host_db[0].split(':')
        
        return {
            'user': user_pass[0],
            'password': user_pass[1],
            'host': host_port[0],
            'port': host_port[1] if len(host_port) > 1 else '3306',
            'database': host_db[1]
        }
