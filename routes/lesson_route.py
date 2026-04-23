from datetime       import date
from flask          import Blueprint, request
from flask_restful  import Api, Resource, reqparse

from models                  import db
from models.group            import Group
from models.lesson           import Lesson
from utils.utils             import get_response
from utils.decorators        import role_required
from utils.reschedule_helper import cancel_and_reschedule

# ============================================================
# PARSERS
# ============================================================
lesson_cancel_parse = reqparse.RequestParser()
lesson_cancel_parse.add_argument("student_id",  type=int, required=True, help="Student ID cannot be blank")
lesson_cancel_parse.add_argument("cancel_date", type=str, required=True, help="cancel_date cannot be blank")
lesson_cancel_parse.add_argument("reason",      type=str)

lesson_move_parse = reqparse.RequestParser()
lesson_move_parse.add_argument("new_date", type=str, required=True, help="new_date cannot be blank")
lesson_move_parse.add_argument("reason",   type=str)

# ============================================================
# BLUEPRINT + API
# ============================================================
lesson_bp = Blueprint("lesson", __name__, url_prefix="/api/lessons")
api       = Api(lesson_bp)


# ============================================================
# RESOURCES
# ============================================================
class LessonCancelResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def post(self):
        """Lesson Cancel API
        Path   - /api/lessons/cancel
        Method - POST
        ---
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
            - name: body
              in: body
              required: true
              schema:
                type: object
                properties:
                    student_id:
                        type: integer
                    cancel_date:
                        type: string
                    reason:
                        type: string
                required: [student_id, cancel_date]
        responses:
            200:
                description: Lesson cancelled and rescheduled
            404:
                description: Student or Lesson not found
        """
        data        = lesson_cancel_parse.parse_args()
        student_id  = data["student_id"]
        cancel_date = data["cancel_date"]
        reason      = data.get("reason")

        group = Group.query.filter_by(student_id=student_id).first()
        if not group:
            return get_response("Student has no group", None, 404), 404

        try:
            c_date = date.fromisoformat(cancel_date)
        except ValueError:
            return get_response("Invalid cancel_date. Use YYYY-MM-DD", None, 400), 400

        result, error = cancel_and_reschedule(group, c_date, reason)
        if error:
            return get_response(error, None, 404), 404

        return get_response("Lesson cancelled and rescheduled", result, 200), 200


class LessonByStudentResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def get(self, student_id):
        """Lessons by Student API
        Path   - /api/lessons/student/<student_id>
        Method - GET
        ---
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
            - name: student_id
              in: path
              type: integer
              required: true
            - name: show_cancelled
              in: query
              type: string
            - name: only_rescheduled
              in: query
              type: string
        responses:
            200:
                description: Return Student's lessons
            404:
                description: Student has no group
        """
        group = Group.query.filter_by(student_id=student_id).first()
        if not group:
            return get_response("Student has no group", None, 404), 404

        only_rescheduled = request.args.get("only_rescheduled", "false").lower() == "true"

        query = Lesson.query.filter_by(group_id=group.id)
        if only_rescheduled:
            query = query.filter_by(is_rescheduled=True)

        lessons = query.order_by(Lesson.lesson_date.asc()).all()
        result  = [Lesson.to_dict(l) for l in lessons]
        return get_response(f"Lessons for student #{student_id}", result, 200), 200


class LessonRestoreResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def patch(self, lesson_id):
        """Lesson Restore API
        Path   - /api/lessons/<lesson_id>/restore
        Method - PATCH
        ---
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
            - name: lesson_id
              in: path
              type: integer
              required: true
        responses:
            200:
                description: Lesson restored
            400:
                description: Lesson is not cancelled
            404:
                description: Not found
        """
        lesson = Lesson.query.filter_by(id=lesson_id).first()
        if not lesson:
            return get_response("Lesson not found", None, 404), 404

        if not lesson.is_cancelled:
            return get_response("Lesson is not cancelled", None, 400), 400

        rescheduled = Lesson.query.filter_by(
            group_id=lesson.group_id, original_date=lesson.lesson_date, is_rescheduled=True
        ).first()
        if rescheduled:
            db.session.delete(rescheduled)

        lesson.is_cancelled  = False
        lesson.cancel_reason = None
        db.session.commit()

        return get_response("Lesson restored", Lesson.to_dict(lesson), 200), 200


class LessonMoveResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def patch(self, lesson_id):
        """Lesson Move API
        Path   - /api/lessons/<lesson_id>/move
        Method - PATCH
        ---
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
            - name: lesson_id
              in: path
              type: integer
              required: true
            - name: body
              in: body
              required: true
              schema:
                type: object
                properties:
                    new_date:
                        type: string
                    reason:
                        type: string
                required: [new_date]
        responses:
            200:
                description: Lesson moved
            400:
                description: Invalid date or conflict
            404:
                description: Not found
        """
        lesson = Lesson.query.filter_by(id=lesson_id).first()
        if not lesson:
            return get_response("Lesson not found", None, 404), 404

        data     = lesson_move_parse.parse_args()
        reason   = data.get("reason")

        try:
            n_date = date.fromisoformat(data["new_date"])
        except ValueError:
            return get_response("Invalid new_date. Use YYYY-MM-DD", None, 400), 400

        # Shanba/Yakshanba tekshirish
        if n_date.weekday() >= 5:
            return get_response("Cannot move lesson to weekend (Sha/Ya)", None, 400), 400

        group = Group.query.filter_by(id=lesson.group_id).first()
        if group.end_date and n_date > group.end_date:
            return get_response("new_date exceeds group end_date", None, 400), 400

        conflict = Lesson.query.filter_by(group_id=lesson.group_id, lesson_date=n_date, is_cancelled=False).first()
        if conflict:
            return get_response(f"{n_date} sanasida allaqachon dars mavjud", None, 400), 400

        old_date             = lesson.lesson_date
        lesson.is_cancelled  = True
        lesson.cancel_reason = reason or "Qo'lda ko'chirildi"

        new_lesson = Lesson(
            group_id=lesson.group_id, lesson_date=n_date, lesson_time=lesson.lesson_time,
            is_rescheduled=True, original_date=old_date,
        )
        db.session.add(new_lesson)
        db.session.commit()

        return get_response("Lesson moved", {
            "cancelled_lesson":   Lesson.to_dict(lesson),
            "rescheduled_lesson": Lesson.to_dict(new_lesson),
        }, 200), 200


# ============================================================
# REGISTER RESOURCES
# ============================================================
api.add_resource(LessonCancelResource,    "/cancel")
api.add_resource(LessonByStudentResource, "/student/<int:student_id>")
api.add_resource(LessonRestoreResource,   "/<int:lesson_id>/restore")
api.add_resource(LessonMoveResource,      "/<int:lesson_id>/move")