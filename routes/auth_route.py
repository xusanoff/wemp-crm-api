from flask              import Blueprint
from flask_restful      import Api, Resource, reqparse
from flask_jwt_extended import create_access_token, get_jwt_identity
from flask_bcrypt       import check_password_hash

from models.user      import User
from utils.utils      import get_response
from utils.decorators import role_required

# ============================================================
# PARSERS
# ============================================================
login_parse = reqparse.RequestParser()
login_parse.add_argument("username", type=str, required=True, help="Username cannot be blank")
login_parse.add_argument("password", type=str, required=True, help="Password cannot be blank")

# ============================================================
# BLUEPRINT + API
# ============================================================
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
api     = Api(auth_bp)


# ============================================================
# RESOURCES
# ============================================================
class LoginResource(Resource):

    def post(self):
        """Auth Login API
        Path   - /api/auth/login
        Method - POST
        ---
        consumes: application/json
        parameters:
            - name: body
              in: body
              required: true
              schema:
                type: object
                properties:
                    username:
                        type: string
                    password:
                        type: string
                required: [username, password]
        responses:
            200:
                description: Return Access Token
            401:
                description: Invalid password
            404:
                description: User not found
        """
        data     = login_parse.parse_args()
        username = data["username"]
        password = data["password"]

        user = User.query.filter_by(username=username).first()
        if not user:
            return get_response("User not found", None, 404), 404

        if not check_password_hash(user.password, password):
            return get_response("Invalid password", None, 401), 401

        access_token = create_access_token(identity=str(user.id))
        # Flat format — frontend d.access_token, d.full_name, d.role ishlatadi
        result_data = {
            "access_token": access_token,
            "user_id":      user.id,
            "full_name":    user.full_name,
            "username":     user.username,
            "role":         user.role,
        }
        return get_response("Login successful", result_data, 200), 200


class MeResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def get(self):
        """Current User API
        Path   - /api/auth/me
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
                description: Return current user info
            404:
                description: User not found
        """
        user_id = int(get_jwt_identity())
        user    = User.query.filter_by(id=user_id).first()
        return get_response("Current user", User.to_dict(user), 200), 200


# ============================================================
# REGISTER RESOURCES
# ============================================================
api.add_resource(LoginResource, "/login")
api.add_resource(MeResource,    "/me")