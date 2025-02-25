# 📌 ระบบจองห้องประชุมและยานพาหนะ

ระบบจองห้องประชุมและยานพาหนะ พัฒนาด้วย Flask (Python) และ MySQL พร้อมระบบแจ้งเตือนผ่าน LINE Messaging API

## 🚀 ฟีเจอร์หลัก
- ระบบ Authentication & RBAC (3 ระดับผู้ใช้)
- ระบบจองห้องประชุมและยานพาหนะ
- ระบบอนุมัติแบบ Multi-Level
- แจ้งเตือนผ่าน LINE Messaging API
- Dashboard และระบบรายงาน
- REST API สำหรับ Mobile/Web

## 🛠 การติดตั้ง

### 1. ติดตั้ง Dependencies
```bash
# สร้าง Virtual Environment
python -m venv venv

# Activate Virtual Environment
# Windows
venv\Scripts\activate

# ติดตั้ง Dependencies
pip install -r requirements.txt
```

### 2. ตั้งค่าฐานข้อมูล
```sql
-- สร้างฐานข้อมูล MySQL
CREATE DATABASE booking_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. ตั้งค่าไฟล์ .env
```env
# Database
DB_HOST=localhost
DB_USER=root
DB_PASS=your_password
DB_NAME=booking_db

# LINE Messaging API
LINE_CHANNEL_ACCESS_TOKEN=your_token
LINE_CHANNEL_SECRET=your_secret

# Flask
FLASK_SECRET_KEY=your_secret_key

# Redis
REDIS_URL=redis://localhost:6379/0
```

### 4. สร้างโครงสร้างฐานข้อมูล
```bash
flask db upgrade
```

## 🚀 วิธีรันระบบ

### รัน Development Server
```bash
# รัน Flask
flask run

# รัน Celery Worker (อีก Terminal)
celery -A app.celery worker --loglevel=info

# รัน Redis (อีก Terminal)
redis-server
```

## 📱 การตั้งค่า LINE Messaging API

1. สร้าง LINE Bot ที่ [LINE Developers Console](https://developers.line.biz/)
2. ตั้งค่า Webhook URL: `https://your-domain.com/webhook`
3. เพิ่ม Channel Access Token และ Channel Secret ในไฟล์ .env

## 🌐 API Endpoints

### ห้องประชุม
```
GET /api/rooms - ดูรายการห้องประชุม
POST /api/rooms/book - จองห้องประชุม
GET /api/rooms/bookings - ดูรายการจองห้องประชุม
PUT /api/rooms/bookings/{id}/approve - อนุมัติการจอง
PUT /api/rooms/bookings/{id}/reject - ปฏิเสธการจอง
```

### ยานพาหนะ
```
GET /api/vehicles - ดูรายการยานพาหนะ
POST /api/vehicles/book - จองยานพาหนะ
GET /api/vehicles/bookings - ดูรายการจองยานพาหนะ
PUT /api/vehicles/bookings/{id}/approve - อนุมัติการจอง
PUT /api/vehicles/bookings/{id}/reject - ปฏิเสธการจอง
```

## 🚀 การ Deploy บน Render

1. สร้าง Account ที่ [Render](https://render.com)
2. เชื่อมต่อ GitHub Repository
3. สร้าง Web Service ใหม่
4. ตั้งค่า Environment Variables ตามไฟล์ .env
5. Deploy!

## 📁 โครงสร้างโปรเจกต์
```
booking/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── tasks/
│   └── templates/
├── tests/
├── migrations/
├── .env
├── .gitignore
├── config.py
├── requirements.txt
└── run.py
```

## 🧪 การรัน Tests
```bash
pytest
```

## 👨‍💻 ทีมพัฒนา
- พัฒนาโดย: [ชื่อทีม/องค์กร]
- Version: 1.0.0
- License: MIT
