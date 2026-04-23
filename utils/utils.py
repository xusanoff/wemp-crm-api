from models import db
from models.user import User


def get_response(message, result, status_code):
    _ = {
        "message":     message,
        "result":      result,
        "status_code": status_code,
    }
    return _


def create_admin():
    # SUPERADMIN yaratish
    found = User.query.filter_by(username="akbarov504", role="SUPERADMIN").first()
    if not found:
        admin = User("Akbarov Akbar", "akbarov504", "12345678", "SUPERADMIN")
        db.session.add(admin)
        db.session.commit()
        print("Successfully created SUPERADMIN.")
    return None