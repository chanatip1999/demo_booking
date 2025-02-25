from flask_babel import Babel
from flask import request, session

babel = Babel()

def init_babel(app):
    """ตั้งค่าระบบหลายภาษา"""
    babel.init_app(app)
    
    # ตั้งค่าภาษาเริ่มต้น
    app.config['BABEL_DEFAULT_LOCALE'] = 'th'
    app.config['BABEL_SUPPORTED_LOCALES'] = ['th', 'en']

@babel.localeselector
def get_locale():
    """เลือกภาษาที่จะใช้"""
    # ลำดับการเลือกภาษา:
    # 1. ภาษาที่ผู้ใช้เลือกไว้ใน session
    # 2. ภาษาที่เบราว์เซอร์ต้องการ
    # 3. ภาษาเริ่มต้น (th)
    if 'language' in session:
        return session['language']
        
    return request.accept_languages.best_match(
        current_app.config['BABEL_SUPPORTED_LOCALES']
    )

def set_language(lang):
    """ตั้งค่าภาษาสำหรับผู้ใช้"""
    if lang in current_app.config['BABEL_SUPPORTED_LOCALES']:
        session['language'] = lang
        return True
    return False
