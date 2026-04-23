from functools import wraps
from models.user import User
from utils.utils import get_response
from flask_jwt_extended import jwt_required, get_jwt_identity


def role_required(role_list):
    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user_id = int(get_jwt_identity())

            user = User.query.filter_by(id=user_id).first()
            if not user:
                return get_response("User not found", None, 404), 404

            if user.role not in role_list:
                return get_response("Permission denied", None, 403), 403

            return func(*args, **kwargs)
        return wrapper
    return decorator
