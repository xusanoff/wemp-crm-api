from datetime       import date as dt_date
from flask          import Blueprint
from flask_restful  import Api, Resource, reqparse
from flask_jwt_extended import get_jwt_identity

from models             import db
from models.user        import User
from models.student     import Student
from models.enrollment  import Enrollment
from models.group       import Group
from models.course      import Course
from models.payment     import Payment, Debt
from models.monthly_debt import MonthlyDebt
from utils.utils        import get_response
from utils.decorators   import role_required
from utils.lesson_generator      import generate_lessons_for_group
from utils.monthly_debt_generator import generate_monthly_debts, current_month_number

VALID_ENROLLMENT_STATUSES = {"active", "finished", "dropped"}
VALID_PAYMENT_TYPES       = {"cash", "click", "payme", "karta"}

# ============================================================
# PARSERS
# ============================================================
student_create_parse = reqparse.RequestParser()
student_create_parse.add_argument("full_name",    type=str, required=True)
student_create_parse.add_argument("phone_number", type=str)
student_create_parse.add_argument("comment",      type=str)
student_create_parse.add_argument("course_id",    type=int, required=True)
student_create_parse.add_argument("teacher_id",   type=int, required=True)
student_create_parse.add_argument("lesson_time",  type=str, required=True)
student_create_parse.add_argument("start_date",   type=str, required=True)

student_update_parse = reqparse.RequestParser()
student_update_parse.add_argument("full_name",    type=str)
student_update_parse.add_argument("phone_number", type=str)
student_update_parse.add_argument("comment",      type=str)
student_update_parse.add_argument("teacher_id",   type=int)
student_update_parse.add_argument("lesson_time",  type=str)
student_update_parse.add_argument("start_date",   type=str)

enrollment_update_parse = reqparse.RequestParser()
enrollment_update_parse.add_argument("status", type=str, required=True)

payment_create_parse = reqparse.RequestParser()
payment_create_parse.add_argument("student_id",   type=int,   required=True)
payment_create_parse.add_argument("payment_type", type=str,   required=True)
payment_create_parse.add_argument("for_month",    type=str,   required=True)
payment_create_parse.add_argument("amount",       type=float, required=True)
payment_create_parse.add_argument("comment",      type=str)

# ============================================================
# BLUEPRINT
# ============================================================
operator_bp = Blueprint("operator", __name__, url_prefix="/api/operator")
api         = Api(operator_bp)


# ============================================================
# HELPER
# ============================================================
def _student_full_info(student):
    """Student + guruh + enrollment + qarz + nechanchi oy."""
    s = Student.to_dict(student)

    group = Group.query.filter_by(student_id=student.id).first()
    if group:
        s["group_id"]        = group.id
        s["course_id"]       = group.course_id
        s["course_name"]     = group.course.name if group.course else None
        s["teacher_id"]      = group.teacher_id
        s["teacher_name"]    = group.teacher.full_name if group.teacher else None
        s["lesson_time"]     = str(group.lesson_time)
        s["start_date"]      = str(group.start_date) if group.start_date else None
        s["end_date"]        = str(group.end_date)   if group.end_date   else None
        s["duration_months"] = group.duration_months

        # Nechanchi oyida o'qiyapti
        s["current_month_number"] = current_month_number(group.start_date) if group.start_date else 1

        enrollment = Enrollment.query.filter_by(student_id=student.id).first()
        if enrollment:
            s["enrollment_id"]     = enrollment.id
            s["enrollment_status"] = enrollment.status

            # Umumiy qarz (eski tizim bilan moslik)
            debt = Debt.query.filter_by(enrollment_id=enrollment.id).first()
            if debt:
                s["total_debt"]     = debt.total_amount
                s["paid_amount"]    = debt.paid_amount
                s["remaining_debt"] = debt.remaining_debt
                s["is_fully_paid"]  = debt.is_fully_paid

            # Oylik qarzlar
            monthly_debts = MonthlyDebt.query.filter_by(
                enrollment_id=enrollment.id
            ).order_by(MonthlyDebt.for_month).all()
            s["monthly_debts"] = [MonthlyDebt.to_dict(md) for md in monthly_debts]

            # Joriy oy qarzi
            from utils.monthly_debt_generator import current_month_str
            cur_month = current_month_str()
            cur_md = next((md for md in monthly_debts if md.for_month == cur_month), None)
            s["current_month_debt"] = MonthlyDebt.to_dict(cur_md) if cur_md else None

            # Muddati o'tgan oylar (to'lanmagan)
            from datetime import date
            today_month = date.today().strftime("%Y-%m")
            overdue = [md for md in monthly_debts if md.for_month < today_month and not md.is_paid]
            s["overdue_months"] = [MonthlyDebt.to_dict(md) for md in overdue]
            s["overdue_count"]  = len(overdue)
        else:
            s["enrollment_id"] = s["enrollment_status"] = None
            s["total_debt"] = s["paid_amount"] = s["remaining_debt"] = 0
            s["is_fully_paid"] = True
            s["monthly_debts"] = []
            s["current_month_debt"] = None
            s["overdue_months"] = []
            s["overdue_count"]  = 0
    else:
        for k in ["group_id","course_id","course_name","teacher_id","teacher_name",
                  "lesson_time","start_date","end_date","duration_months",
                  "enrollment_id","enrollment_status","current_month_number"]:
            s[k] = None
        s["total_debt"] = s["paid_amount"] = s["remaining_debt"] = 0
        s["is_fully_paid"] = True
        s["monthly_debts"] = []
        s["current_month_debt"] = None
        s["overdue_months"] = []
        s["overdue_count"]  = 0

    return s


# ============================================================
# STUDENT
# ============================================================
class StudentResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def get(self, student_id):
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return get_response("Student not found", None, 404), 404
        return get_response("Student found", _student_full_info(student), 200), 200

    @role_required(["SUPERADMIN", "ADMIN"])
    def patch(self, student_id):
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return get_response("Student not found", None, 404), 404

        data = student_update_parse.parse_args()

        if data.get("full_name"):
            student.full_name = data["full_name"]
        if data.get("phone_number"):
            existing = Student.query.filter_by(phone_number=data["phone_number"]).first()
            if existing and existing.id != student_id:
                return get_response("Phone number already registered", None, 400), 400
            student.phone_number = data["phone_number"]
        if data.get("comment") is not None:
            student.comment = data["comment"]

        group = Group.query.filter_by(student_id=student_id).first()
        if group:
            if data.get("teacher_id") is not None:
                teacher = User.query.filter_by(id=data["teacher_id"]).first()
                if not teacher:
                    return get_response("Teacher not found", None, 404), 404
                group.teacher_id = teacher.id
            if data.get("lesson_time"):
                group.lesson_time = data["lesson_time"]
            if data.get("start_date"):
                try:
                    group.start_date = dt_date.fromisoformat(data["start_date"])
                except ValueError:
                    return get_response("Invalid start_date. Use YYYY-MM-DD", None, 400), 400
            db.session.commit()
            generate_lessons_for_group(group)
        else:
            db.session.commit()

        return get_response("Student updated", _student_full_info(student), 200), 200

    @role_required(["SUPERADMIN", "ADMIN"])
    def delete(self, student_id):
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return get_response("Student not found", None, 404), 404
        db.session.delete(student)
        db.session.commit()
        return get_response("Student deleted", None, 200), 200


class StudentListCreateResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def get(self):
        students = Student.query.order_by(Student.created_at.desc()).all()
        result   = [_student_full_info(s) for s in students]
        return get_response("Student List", result, 200), 200

    @role_required(["SUPERADMIN", "ADMIN"])
    def post(self):
        user_id = int(get_jwt_identity())
        data    = student_create_parse.parse_args()

        phone_num  = data.get("phone_number")
        course_id  = data["course_id"]
        teacher_id = data["teacher_id"]

        if phone_num and Student.query.filter_by(phone_number=phone_num).first():
            return get_response("Phone number already registered", None, 400), 400

        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return get_response("Course not found", None, 404), 404

        teacher = User.query.filter_by(id=teacher_id).first()
        if not teacher:
            return get_response("Teacher not found", None, 404), 404

        try:
            start_date = dt_date.fromisoformat(data["start_date"])
        except ValueError:
            return get_response("Invalid start_date. Use YYYY-MM-DD", None, 400), 400

        # 1. O'quvchi
        new_student = Student(
            full_name    = data["full_name"],
            phone_number = phone_num,
            comment      = data.get("comment"),
            created_by   = user_id,
        )
        db.session.add(new_student)
        db.session.flush()

        # 2. Shaxsiy guruh
        new_group = Group(
            name        = f"{new_student.full_name} — {course.name}",
            course_id   = course_id,
            student_id  = new_student.id,
            teacher_id  = teacher_id,
            lesson_time = data["lesson_time"],
            start_date  = start_date,
        )
        db.session.add(new_group)
        db.session.flush()

        # 3. Enrollment
        new_enrollment = Enrollment(
            student_id = new_student.id,
            group_id   = new_group.id,
            status     = "active",
        )
        db.session.add(new_enrollment)
        db.session.flush()

        # 4. Umumiy qarz (eski tizim bilan moslik)
        total_debt = course.total_price
        new_debt   = Debt(
            student_id    = new_student.id,
            enrollment_id = new_enrollment.id,
            total_amount  = total_debt,
        )
        db.session.add(new_debt)

        # 5. Oylik qarzlar — har oy uchun alohida
        monthly_debts = generate_monthly_debts(
            student_id    = new_student.id,
            enrollment_id = new_enrollment.id,
            course        = course,
            start_date    = start_date,
        )

        db.session.commit()

        # 6. Darslar
        lesson_count = generate_lessons_for_group(new_group)

        result = _student_full_info(new_student)
        result["lesson_count"] = lesson_count
        result["info"] = (
            f"{new_student.full_name} '{course.name}' kursiga yozildi. "
            f"O'qituvchi: {teacher.full_name}. "
            f"Dars: {data['lesson_time']}, {data['start_date']} dan. "
            f"Oylik to'lov: {course.price:,.0f} so'm × {course.duration_months} oy "
            f"= {total_debt:,.0f} so'm. "
            f"{lesson_count} ta dars (Du-Ju) yaratildi."
        )

        return get_response("Student created", result, 200), 200


# ============================================================
# ENROLLMENT STATUS
# ============================================================
class EnrollmentUpdateResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def patch(self, enrollment_id):
        enrollment = Enrollment.query.filter_by(id=enrollment_id).first()
        if not enrollment:
            return get_response("Enrollment not found", None, 404), 404

        data   = enrollment_update_parse.parse_args()
        status = data["status"].lower()

        if status not in VALID_ENROLLMENT_STATUSES:
            return get_response(f"Invalid status. Valid: {VALID_ENROLLMENT_STATUSES}", None, 400), 400

        enrollment.status = status
        db.session.commit()
        return get_response("Enrollment status updated", Enrollment.to_dict(enrollment), 200), 200


# ============================================================
# PAYMENT — oylik qarz bilan bog'langan
# ============================================================
class PaymentResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def get(self, payment_id):
        payment = Payment.query.filter_by(id=payment_id).first()
        if not payment:
            return get_response("Payment not found", None, 404), 404
        return get_response("Payment found", Payment.to_dict(payment), 200), 200

    @role_required(["SUPERADMIN", "ADMIN"])
    def delete(self, payment_id):
        payment = Payment.query.filter_by(id=payment_id).first()
        if not payment:
            return get_response("Payment not found", None, 404), 404

        # Umumiy qarzni qaytarish
        if payment.debt_id:
            debt = Debt.query.filter_by(id=payment.debt_id).first()
            if debt:
                debt.paid_amount = max(0.0, debt.paid_amount - payment.amount)

        # Oylik qarzdan ham ayirish
        md = MonthlyDebt.query.filter_by(
            student_id = payment.student_id,
            for_month  = payment.for_month,
        ).first()
        if md:
            md.paid_amount = max(0.0, md.paid_amount - payment.amount)

        db.session.delete(payment)
        db.session.commit()
        return get_response("Payment deleted", None, 200), 200


class PaymentListCreateResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def get(self):
        payments = Payment.query.order_by(Payment.payment_date.desc()).all()
        result   = [Payment.to_dict(p) for p in payments]
        return get_response("Payment List", result, 200), 200

    @role_required(["SUPERADMIN", "ADMIN"])
    def post(self):
        user_id      = int(get_jwt_identity())
        data         = payment_create_parse.parse_args()
        student_id   = data["student_id"]
        payment_type = data["payment_type"].lower()
        for_month    = data["for_month"]
        amount       = data["amount"]

        if payment_type not in VALID_PAYMENT_TYPES:
            return get_response(f"Invalid payment_type. Valid: {VALID_PAYMENT_TYPES}", None, 400), 400

        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return get_response("Student not found", None, 404), 404

        # Umumiy qarz
        active_enrollment = Enrollment.query.filter_by(student_id=student_id, status="active").first()
        debt = None
        if active_enrollment:
            debt = Debt.query.filter_by(enrollment_id=active_enrollment.id).first()

        new_payment = Payment(
            student_id   = student_id,
            payment_type = payment_type,
            for_month    = for_month,
            amount       = amount,
            comment      = data.get("comment"),
            created_by   = user_id,
            debt_id      = debt.id if debt else None,
        )
        db.session.add(new_payment)

        # Umumiy qarzni kamaytirish
        if debt:
            debt.paid_amount += amount

        # Oylik qarzni kamaytirish — shu oy uchun
        if active_enrollment:
            md = MonthlyDebt.query.filter_by(
                enrollment_id = active_enrollment.id,
                for_month     = for_month,
            ).first()
            if md:
                md.paid_amount = min(md.amount, md.paid_amount + amount)

        db.session.commit()

        return get_response("Payment recorded", {
            **Payment.to_dict(new_payment),
            "debt_status": Debt.to_dict(debt) if debt else None,
        }, 200), 200


# ============================================================
# DEBT
# ============================================================
class StudentDebtResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def get(self, student_id):
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return get_response("Student not found", None, 404), 404

        debts = Debt.query.filter_by(student_id=student_id).all()

        enrollment = Enrollment.query.filter_by(student_id=student_id).first()
        monthly_debts = []
        if enrollment:
            monthly_debts = MonthlyDebt.query.filter_by(
                enrollment_id=enrollment.id
            ).order_by(MonthlyDebt.for_month).all()

        return get_response("Student Debt Info", {
            "student_id":      student_id,
            "student_name":    student.full_name,
            "total_debt":      sum(d.total_amount   for d in debts),
            "total_paid":      sum(d.paid_amount    for d in debts),
            "total_remaining": sum(d.remaining_debt for d in debts),
            "monthly_debts":   [MonthlyDebt.to_dict(md) for md in monthly_debts],
        }, 200), 200


# ============================================================
# REGISTER
# ============================================================
api.add_resource(StudentListCreateResource, "/students")
api.add_resource(StudentResource,           "/students/<int:student_id>")
api.add_resource(EnrollmentUpdateResource,  "/enrollments/<int:enrollment_id>")
api.add_resource(PaymentListCreateResource, "/payments")
api.add_resource(PaymentResource,           "/payments/<int:payment_id>")
api.add_resource(StudentDebtResource,       "/debts/student/<int:student_id>")