from flask          import Blueprint
from flask_restful  import Api, Resource, reqparse

from models         import db
from models.course  import Course
from utils.utils    import get_response
from utils.decorators import role_required

# ============================================================
# PARSERS
# ============================================================
course_create_parse = reqparse.RequestParser()
course_create_parse.add_argument("name",            type=str,   required=True, help="Name cannot be blank")
course_create_parse.add_argument("price",           type=float, required=True, help="Price cannot be blank")
course_create_parse.add_argument("duration_months", type=int,   default=1)

course_update_parse = reqparse.RequestParser()
course_update_parse.add_argument("name",            type=str)
course_update_parse.add_argument("price",           type=float)
course_update_parse.add_argument("duration_months", type=int)

# ============================================================
# BLUEPRINT + API
# ============================================================
course_bp = Blueprint("course", __name__, url_prefix="/api/courses")
api       = Api(course_bp)


# ============================================================
# RESOURCES
# ============================================================
class CourseResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def get(self, course_id):
        """Course Get API
        Path   - /api/courses/<course_id>
        Method - GET
        ---
        consumes: application/json
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
              description: Bearer token for authentication
            - name: course_id
              in: path
              type: integer
              required: true
              description: Enter Course ID
        responses:
            200:
                description: Return a Course
            404:
                description: Course not found
        """
        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return get_response("Course not found", None, 404), 404
        return get_response("Course found", Course.to_dict(course), 200), 200

    @role_required(["SUPERADMIN", "ADMIN"])
    def patch(self, course_id):
        """Course Update API
        Path   - /api/courses/<course_id>
        Method - PATCH
        ---
        consumes: application/json
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
              description: Bearer token for authentication
            - name: course_id
              in: path
              type: integer
              required: true
              description: Enter Course ID
            - name: body
              in: body
              required: true
              schema:
                type: object
                properties:
                    name:
                        type: string
                    price:
                        type: number
                    duration_months:
                        type: integer
        responses:
            200:
                description: Course successfully updated
            400:
                description: duration_months must be a positive integer
            404:
                description: Course not found
        """
        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return get_response("Course not found", None, 404), 404

        data = course_update_parse.parse_args()

        if data.get("name"):
            course.name = data["name"]
        if data.get("price") is not None:
            course.price = data["price"]
        if data.get("duration_months") is not None:
            if data["duration_months"] < 1:
                return get_response("duration_months must be a positive integer", None, 400), 400
            course.duration_months = data["duration_months"]

        db.session.commit()
        return get_response("Course successfully updated", Course.to_dict(course), 200), 200

    @role_required(["SUPERADMIN", "ADMIN"])
    def delete(self, course_id):
        """Course Delete API
        Path   - /api/courses/<course_id>
        Method - DELETE
        ---
        consumes: application/json
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
              description: Bearer token for authentication
            - name: course_id
              in: path
              type: integer
              required: true
              description: Enter Course ID
        responses:
            200:
                description: Course successfully deleted
            404:
                description: Course not found
        """
        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return get_response("Course not found", None, 404), 404

        db.session.delete(course)
        db.session.commit()
        return get_response("Course successfully deleted", None, 200), 200


class CourseListCreateResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def get(self):
        """Course List API
        Path   - /api/courses
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
                description: Return Course List
        """
        courses = Course.query.all()
        result  = [Course.to_dict(c) for c in courses]
        return get_response("Course List", result, 200), 200

    @role_required(["SUPERADMIN", "ADMIN"])
    def post(self):
        """Course Create API
        Path   - /api/courses
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
                    name:
                        type: string
                    price:
                        type: number
                    duration_months:
                        type: integer
                required: [name, price]
        responses:
            200:
                description: Course successfully created
            400:
                description: name and price are required or invalid duration_months
        """
        data            = course_create_parse.parse_args()
        name            = data["name"]
        price           = data["price"]
        duration_months = data["duration_months"]

        if duration_months < 1:
            return get_response("duration_months must be a positive integer", None, 400), 400

        new_course = Course(name, price, duration_months)
        db.session.add(new_course)
        db.session.commit()
        return get_response("Course successfully created", Course.to_dict(new_course), 200), 200


# ============================================================
# REGISTER RESOURCES
# ============================================================
api.add_resource(CourseListCreateResource, "/")
api.add_resource(CourseResource,           "/<int:course_id>")