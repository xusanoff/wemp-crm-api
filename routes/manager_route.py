from datetime       import date
from flask          import Blueprint, request
from flask_restful  import Api, Resource, reqparse
from sqlalchemy     import func

from models              import db
from models.lesson       import Lesson
from models.attendance   import Attendance
from models.enrollment   import Enrollment
from models.payment      import Payment, Debt
from models.student      import Student
from models.group        import Group
from models.monthly_debt import MonthlyDebt
from models.course_module import CourseModule, ModuleLesson
from utils.utils         import get_response
from utils.decorators    import role_required

VALID_ATTENDANCE_STATUSES = {"keldi", "kelmadi"}
VALID_LESSON_TYPES        = {"dars", "savol-javob", "project"}

# ── PARSERS ──────────────────────────────────────────────────
attendance_mark_parse = reqparse.RequestParser()
attendance_mark_parse.add_argument("lesson_id",        type=int,  required=True, location="json")
attendance_mark_parse.add_argument("records",          type=list, required=True, location="json")

attendance_update_parse = reqparse.RequestParser()
attendance_update_parse.add_argument("status",            type=str, required=True)
attendance_update_parse.add_argument("arrival_time",      type=str)
attendance_update_parse.add_argument("module_id",         type=int)
attendance_update_parse.add_argument("module_lesson_id",  type=int)
attendance_update_parse.add_argument("lesson_type",       type=str)

# ── BLUEPRINT ─────────────────────────────────────────────────
manager_bp = Blueprint("manager", __name__, url_prefix="/api/manager")
api        = Api(manager_bp)


# ── STUDENTS ─────────────────────────────────────────────────
class StudentListResource(Resource):
    decorators = [role_required(["SUPERADMIN", "ADMIN"])]

    def get(self):
        students = Student.query.order_by(Student.full_name).all()
        result   = []
        for s in students:
            group = Group.query.filter_by(student_id=s.id).first()
            enr   = Enrollment.query.filter_by(student_id=s.id, status="active").first()
            result.append({
                "student_id":        s.id,
                "full_name":         s.full_name,
                "phone_number":      s.phone_number,
                "group_id":          group.id                   if group else None,
                "course_name":       group.course.name          if group and group.course else None,
                "teacher_name":      group.teacher.full_name    if group and group.teacher else None,
                "lesson_time":       str(group.lesson_time)     if group else None,
                "start_date":        str(group.start_date)      if group and group.start_date else None,
                "enrollment_id":     enr.id     if enr else None,
                "enrollment_status": enr.status if enr else None,
            })
        return get_response("Student List", result, 200), 200


class StudentLessonsResource(Resource):
    decorators = [role_required(["SUPERADMIN", "ADMIN"])]

    def get(self, student_id):
        group = Group.query.filter_by(student_id=student_id).first()
        if not group:
            return get_response("Student has no group", None, 404), 404
        lessons = Lesson.query.filter_by(group_id=group.id).order_by(Lesson.lesson_date.asc()).all()
        return get_response("Student Lessons", [Lesson.to_dict(l) for l in lessons], 200), 200


# ── ATTENDANCE ───────────────────────────────────────────────
class AttendanceListMarkResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def get(self):
        lesson_id  = request.args.get("lesson_id",  type=int)
        student_id = request.args.get("student_id", type=int)

        query = Attendance.query

        if lesson_id:
            query = query.filter_by(lesson_id=lesson_id)
        if student_id:
            group = Group.query.filter_by(student_id=student_id).first()
            if group:
                lesson_ids = [l.id for l in Lesson.query.filter_by(group_id=group.id).all()]
                if lesson_ids:
                    query = query.filter(Attendance.lesson_id.in_(lesson_ids))
                else:
                    return get_response("Attendance List", [], 200), 200
            else:
                return get_response("Attendance List", [], 200), 200

        records = query.all()
        result  = []
        for a in records:
            student = Student.query.filter_by(id=a.student_id).first()
            result.append({
                **Attendance.to_dict(a),
                "student_name": student.full_name if student else None,
            })
        return get_response("Attendance List", result, 200), 200

    @role_required(["SUPERADMIN", "ADMIN"])
    def post(self):
        """
        Davomat belgilash.
        records ichida:
          { student_id, status, arrival_time?, module_id?, module_lesson_id?, lesson_type? }
        """
        data      = attendance_mark_parse.parse_args()
        lesson_id = data["lesson_id"]
        records   = data["records"]

        lesson = Lesson.query.filter_by(id=lesson_id).first()
        if not lesson:
            return get_response("Lesson not found", None, 404), 404

        saved  = []
        errors = []

        for rec in records:
            student_id       = rec.get("student_id")
            status           = (rec.get("status") or "").lower()
            arrival_time     = rec.get("arrival_time") if status == "keldi" else None
            module_id        = rec.get("module_id")
            module_lesson_id = rec.get("module_lesson_id")
            lesson_type      = rec.get("lesson_type", "dars")

            if status not in VALID_ATTENDANCE_STATUSES:
                errors.append({"student_id": student_id, "error": f"invalid status '{status}'"})
                continue

            if lesson_type not in VALID_LESSON_TYPES:
                lesson_type = "dars"

            student  = Student.query.filter_by(id=student_id).first()
            existing = Attendance.query.filter_by(lesson_id=lesson_id, student_id=student_id).first()

            if existing:
                existing.status           = status
                existing.arrival_time     = arrival_time
                existing.module_id        = module_id
                existing.module_lesson_id = module_lesson_id
                existing.lesson_type      = lesson_type
                saved.append({**Attendance.to_dict(existing), "student_name": student.full_name if student else None})
            else:
                new_att = Attendance(
                    lesson_id        = lesson_id,
                    student_id       = student_id,
                    status           = status,
                    arrival_time     = arrival_time,
                    module_id        = module_id,
                    module_lesson_id = module_lesson_id,
                    lesson_type      = lesson_type,
                )
                db.session.add(new_att)
                db.session.flush()
                saved.append({**Attendance.to_dict(new_att), "student_name": student.full_name if student else None})

        db.session.commit()

        # Telegram bot — darhol xabar
        if saved:
            try:
                from bot.hooks import notify_attendance
                notify_attendance(saved, {
                    "lesson_date": lesson.lesson_date.isoformat() if lesson.lesson_date else "",
                    "lesson_time": str(lesson.lesson_time),
                })
            except Exception as bot_err:
                print(f"[BOT] hook error: {bot_err}")

        return get_response("Attendance marked", {"saved": saved, "errors": errors}, 200), 200


class AttendanceResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def patch(self, att_id):
        att = Attendance.query.filter_by(id=att_id).first()
        if not att:
            return get_response("Attendance not found", None, 404), 404

        data   = attendance_update_parse.parse_args()
        status = data["status"].lower()

        if status not in VALID_ATTENDANCE_STATUSES:
            return get_response(f"Invalid status. Valid: {list(VALID_ATTENDANCE_STATUSES)}", None, 400), 400

        att.status       = status
        att.arrival_time = data.get("arrival_time") if status == "keldi" else None

        if data.get("module_id") is not None:
            att.module_id = data["module_id"]
        if data.get("module_lesson_id") is not None:
            att.module_lesson_id = data["module_lesson_id"]
        if data.get("lesson_type") and data["lesson_type"] in VALID_LESSON_TYPES:
            att.lesson_type = data["lesson_type"]

        db.session.commit()
        return get_response("Attendance updated", Attendance.to_dict(att), 200), 200

    @role_required(["SUPERADMIN", "ADMIN"])
    def delete(self, att_id):
        att = Attendance.query.filter_by(id=att_id).first()
        if not att:
            return get_response("Attendance not found", None, 404), 404
        db.session.delete(att)
        db.session.commit()
        return get_response("Attendance deleted", None, 200), 200


# ── PAYMENTS ─────────────────────────────────────────────────
class PaymentsByStudentResource(Resource):
    decorators = [role_required(["SUPERADMIN", "ADMIN"])]

    def get(self, student_id):
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return get_response("Student not found", None, 404), 404
        payments = Payment.query.filter_by(student_id=student_id).order_by(Payment.payment_date.desc()).all()
        debts    = Debt.query.filter_by(student_id=student_id).all()
        return get_response(f"Payments for #{student_id}", {
            "student":         Student.to_dict(student),
            "payments":        [Payment.to_dict(p) for p in payments],
            "total_debt":      sum(d.total_amount   for d in debts),
            "total_paid":      sum(d.paid_amount    for d in debts),
            "total_remaining": sum(d.remaining_debt for d in debts),
        }, 200), 200


class PaymentsSummaryResource(Resource):
    decorators = [role_required(["SUPERADMIN", "ADMIN"])]

    def get(self):
        today     = date.today()
        cur_month = today.strftime("%Y-%m")
        from dateutil.relativedelta import relativedelta
        prev_month = (today - relativedelta(months=1)).strftime("%Y-%m")

        cur_month_debts  = MonthlyDebt.query.filter_by(for_month=cur_month).all()
        expected_income  = sum(md.amount      for md in cur_month_debts)
        received_income  = sum(md.paid_amount for md in cur_month_debts)
        cur_remaining    = sum(md.remaining   for md in cur_month_debts)

        prev_month_debts = MonthlyDebt.query.filter_by(for_month=prev_month).all()
        prev_unpaid      = [md for md in prev_month_debts if not md.is_paid]
        prev_unpaid_total= sum(md.remaining for md in prev_unpaid)
        prev_unpaid_students = []
        for md in prev_unpaid:
            s = Student.query.filter_by(id=md.student_id).first()
            prev_unpaid_students.append({
                "student_id":   md.student_id,
                "student_name": s.full_name if s else None,
                "for_month":    md.for_month,
                "amount":       md.amount,
                "paid_amount":  md.paid_amount,
                "remaining":    md.remaining,
            })

        type_rows = db.session.query(
            Payment.payment_type,
            func.sum(Payment.amount).label("total"),
            func.count(Payment.id).label("count"),
        ).group_by(Payment.payment_type).all()
        type_bd      = {r.payment_type: {"total": r.total, "count": r.count} for r in type_rows}
        online_types = ["karta","payme","click"]
        cash_total   = type_bd.get("cash",{}).get("total",0) or 0
        cash_count   = type_bd.get("cash",{}).get("count",0) or 0
        online_total = sum((type_bd.get(t,{}).get("total",0) or 0) for t in online_types)
        online_count = sum((type_bd.get(t,{}).get("count",0) or 0) for t in online_types)

        month_rows = db.session.query(
            Payment.for_month,
            func.sum(Payment.amount).label("total"),
        ).group_by(Payment.for_month).order_by(Payment.for_month).all()

        return get_response("Payments Summary", {
            "current_month":           cur_month,
            "current_month_expected":  expected_income,
            "current_month_received":  received_income,
            "current_month_remaining": cur_remaining,
            "current_month_students":  len(cur_month_debts),
            "prev_month":              prev_month,
            "prev_month_unpaid":       prev_unpaid_total,
            "prev_month_debtors":      prev_unpaid_students,
            "prev_month_debtor_count": len(prev_unpaid_students),
            "by_month":    [{"for_month": r.for_month, "total": r.total} for r in month_rows],
            "by_type":     type_bd,
            "cash":        {"total": cash_total,   "count": cash_count},
            "online":      {"total": online_total, "count": online_count},
            "grand_total": cash_total + online_total,
        }, 200), 200


# ── REGISTER ─────────────────────────────────────────────────
api.add_resource(StudentListResource,        "/students")
api.add_resource(StudentLessonsResource,     "/students/<int:student_id>/lessons")
api.add_resource(AttendanceListMarkResource, "/attendance")
api.add_resource(AttendanceResource,         "/attendance/<int:att_id>")
api.add_resource(PaymentsByStudentResource,  "/payments/student/<int:student_id>")
api.add_resource(PaymentsSummaryResource,    "/payments/summary")