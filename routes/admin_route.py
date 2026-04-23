from flask              import Blueprint
from flask_restful      import Api, Resource, reqparse
from flask_jwt_extended import get_jwt_identity
from flask_bcrypt       import generate_password_hash

from models             import db
from models.user        import User
from utils.utils        import get_response
from utils.decorators   import role_required

# Rollar: SUPERADMIN — foydalanuvchi qo'sha oladi
#         ADMIN      — foydalanuvchi qo'sha olmaydi, boshqa hamma funksiyaga ega
VALID_ROLES = {"SUPERADMIN", "ADMIN"}

# ============================================================
# PARSERS
# ============================================================
user_create_parse = reqparse.RequestParser()
user_create_parse.add_argument("full_name", type=str, required=True, help="Full name cannot be blank")
user_create_parse.add_argument("username",  type=str, required=True, help="Username cannot be blank")
user_create_parse.add_argument("password",  type=str, required=True, help="Password cannot be blank")
user_create_parse.add_argument("role",      type=str, required=True, help="Role cannot be blank")

user_update_parse = reqparse.RequestParser()
user_update_parse.add_argument("full_name", type=str)
user_update_parse.add_argument("username",  type=str)
user_update_parse.add_argument("password",  type=str)
user_update_parse.add_argument("role",      type=str)

# ============================================================
# BLUEPRINT + API
# ============================================================
admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
api      = Api(admin_bp)


# ============================================================
# RESOURCES
# ============================================================
class UserResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def get(self, user_id):
        """User Get API
        Path   - /api/admin/users/<user_id>
        Method - GET
        ---
        consumes: application/json
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
              description: Bearer token for authentication
            - name: user_id
              in: path
              type: integer
              required: true
        responses:
            200:
                description: Return a User
            404:
                description: User not found
        """
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return get_response("User not found", None, 404), 404
        return get_response("User found", User.to_dict(user), 200), 200

    @role_required(["SUPERADMIN", "ADMIN"])
    def patch(self, user_id):
        """User Update API
        Path   - /api/admin/users/<user_id>
        Method - PATCH
        ---
        consumes: application/json
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
              description: Bearer token for authentication
            - name: user_id
              in: path
              type: integer
              required: true
            - name: body
              in: body
              required: true
              schema:
                type: object
                properties:
                    full_name:
                        type: string
                    username:
                        type: string
                    password:
                        type: string
                    role:
                        type: string
        responses:
            200:
                description: User successfully updated
            400:
                description: Invalid role or Username already taken
            404:
                description: User not found
        """
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return get_response("User not found", None, 404), 404

        data = user_update_parse.parse_args()

        if data.get("full_name"):
            user.full_name = data["full_name"]

        if data.get("username"):
            existing = User.query.filter_by(username=data["username"]).first()
            if existing and existing.id != user_id:
                return get_response("Username already taken", None, 400), 400
            user.username = data["username"]

        if data.get("role"):
            role = data["role"].upper()
            if role not in VALID_ROLES:
                return get_response(f"Invalid role. Valid: {VALID_ROLES}", None, 400), 400
            user.role = role

        if data.get("password"):
            user.password = generate_password_hash(data["password"]).decode("utf-8")

        db.session.commit()
        return get_response("User successfully updated", User.to_dict(user), 200), 200

    @role_required(["SUPERADMIN", "ADMIN"])
    def delete(self, user_id):
        """User Delete API
        Path   - /api/admin/users/<user_id>
        Method - DELETE
        ---
        consumes: application/json
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
              description: Bearer token for authentication
            - name: user_id
              in: path
              type: integer
              required: true
        responses:
            200:
                description: User successfully deleted
            400:
                description: You cannot delete yourself
            404:
                description: User not found
        """
        current_id = int(get_jwt_identity())
        if current_id == user_id:
            return get_response("You cannot delete yourself", None, 400), 400

        user = User.query.filter_by(id=user_id).first()
        if not user:
            return get_response("User not found", None, 404), 404

        db.session.delete(user)
        db.session.commit()
        return get_response("User successfully deleted", None, 200), 200


class UserListCreateResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def get(self):
        """User List API
        Path   - /api/admin/users
        Method - GET
        ---
        consumes: application/json
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
              description: Bearer token for authentication
        responses:
            200:
                description: Return User List
        """
        users  = User.query.order_by(User.created_at.desc()).all()
        result = [User.to_dict(u) for u in users]
        return get_response("User List", result, 200), 200

    @role_required(["SUPERADMIN"])
    def post(self):
        """User Create API — faqat SUPERADMIN
        Path   - /api/admin/users
        Method - POST
        ---
        consumes: application/json
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
              description: Bearer token for authentication
            - name: body
              in: body
              required: true
              schema:
                type: object
                properties:
                    full_name:
                        type: string
                    username:
                        type: string
                    password:
                        type: string
                    role:
                        type: string
                required: [full_name, username, password, role]
        responses:
            200:
                description: User successfully created
            400:
                description: Invalid role or Username already exists
            403:
                description: Only SUPERADMIN can create users
        """
        data      = user_create_parse.parse_args()
        full_name = data["full_name"]
        username  = data["username"]
        password  = data["password"]
        role      = data["role"].upper()

        if role not in VALID_ROLES:
            return get_response(f"Invalid role. Valid: {VALID_ROLES}", None, 400), 400

        if User.query.filter_by(username=username).first():
            return get_response("Username already exists", None, 400), 400

        new_user = User(full_name, username, password, role)
        db.session.add(new_user)
        db.session.commit()
        return get_response("User successfully created", User.to_dict(new_user), 200), 200


# ============================================================
# REGISTER RESOURCES
# ============================================================
api.add_resource(UserListCreateResource, "/users")
api.add_resource(UserResource,           "/users/<int:user_id>")