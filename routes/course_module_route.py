"""
Kurs modullari va modul darslarini boshqarish.
Fayl yuklash (PDF / rasm) ham shu yerda.
"""
import os
import uuid
from flask          import Blueprint, request, send_from_directory
from flask_restful  import Api, Resource, reqparse

from models                  import db
from models.course           import Course
from models.course_module    import CourseModule, ModuleLesson
from utils.utils             import get_response
from utils.decorators        import role_required

UPLOAD_FOLDER = "/tmp/uploads"
ALLOWED_EXT   = {"pdf", "png", "jpg", "jpeg", "webp"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)




def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def get_file_type(filename):
    ext = filename.rsplit(".", 1)[1].lower()
    return "pdf" if ext == "pdf" else "image"


# ── PARSERS ──────────────────────────────────────────────────
module_create_parse = reqparse.RequestParser()
module_create_parse.add_argument("title",       type=str, required=True, help="Title required")
module_create_parse.add_argument("order_num",   type=int, default=1)
module_create_parse.add_argument("description", type=str)

module_update_parse = reqparse.RequestParser()
module_update_parse.add_argument("title",       type=str)
module_update_parse.add_argument("order_num",   type=int)
module_update_parse.add_argument("description", type=str)

lesson_create_parse = reqparse.RequestParser()
lesson_create_parse.add_argument("title",       type=str, required=True, help="Title required")
lesson_create_parse.add_argument("order_num",   type=int, default=1)
lesson_create_parse.add_argument("description", type=str)

lesson_update_parse = reqparse.RequestParser()
lesson_update_parse.add_argument("title",       type=str)
lesson_update_parse.add_argument("order_num",   type=int)
lesson_update_parse.add_argument("description", type=str)

# ── BLUEPRINT ─────────────────────────────────────────────────
course_module_bp = Blueprint("course_module", __name__, url_prefix="/api/course-modules")
api = Api(course_module_bp)

# Fayllarni xizmat qilish uchun alohida blueprint
file_bp = Blueprint("files", __name__, url_prefix="/uploads")

@file_bp.route("/<path:filename>")
def serve_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ── MODULLAR ─────────────────────────────────────────────────
class CourseModuleListResource(Resource):
    """GET /api/course-modules/?course_id=1  — barcha modullar"""
    decorators = [role_required(["SUPERADMIN", "ADMIN"])]

    def get(self):
        course_id = request.args.get("course_id", type=int)
        q = CourseModule.query
        if course_id:
            q = q.filter_by(course_id=course_id)
        modules = q.order_by(CourseModule.order_num).all()
        result  = [CourseModule.to_dict(m, include_lessons=True) for m in modules]
        return get_response("Modules", result, 200), 200

    def post(self):
        """Yangi modul qo'shish"""
        course_id = request.args.get("course_id", type=int)
        if not course_id:
            return get_response("course_id required", None, 400), 400
        if not Course.query.filter_by(id=course_id).first():
            return get_response("Course not found", None, 404), 404

        data = module_create_parse.parse_args()
        m    = CourseModule(
            course_id   = course_id,
            title       = data["title"],
            order_num   = data.get("order_num") or 1,
            description = data.get("description"),
        )
        db.session.add(m)
        db.session.commit()
        return get_response("Module created", CourseModule.to_dict(m, include_lessons=True), 200), 200


class CourseModuleResource(Resource):
    decorators = [role_required(["SUPERADMIN", "ADMIN"])]

    def get(self, module_id):
        m = CourseModule.query.filter_by(id=module_id).first()
        if not m:
            return get_response("Module not found", None, 404), 404
        return get_response("Module", CourseModule.to_dict(m, include_lessons=True), 200), 200

    def patch(self, module_id):
        m = CourseModule.query.filter_by(id=module_id).first()
        if not m:
            return get_response("Module not found", None, 404), 404
        data = module_update_parse.parse_args()
        if data.get("title"):       m.title       = data["title"]
        if data.get("order_num"):   m.order_num   = data["order_num"]
        if data.get("description") is not None: m.description = data["description"]
        db.session.commit()
        return get_response("Module updated", CourseModule.to_dict(m, include_lessons=True), 200), 200

    def delete(self, module_id):
        m = CourseModule.query.filter_by(id=module_id).first()
        if not m:
            return get_response("Module not found", None, 404), 404
        # Fayllarni ham o'chirish
        for lesson in m.lessons:
            if lesson.file_path and os.path.exists(lesson.file_path):
                os.remove(lesson.file_path)
        db.session.delete(m)
        db.session.commit()
        return get_response("Module deleted", None, 200), 200


# ── DARSLAR ──────────────────────────────────────────────────
class ModuleLessonListResource(Resource):
    """GET /api/course-modules/<id>/lessons"""
    decorators = [role_required(["SUPERADMIN", "ADMIN"])]

    def get(self, module_id):
        m = CourseModule.query.filter_by(id=module_id).first()
        if not m:
            return get_response("Module not found", None, 404), 404
        lessons = m.lessons.all()
        return get_response("Lessons", [ModuleLesson.to_dict(l) for l in lessons], 200), 200

    def post(self, module_id):
        m = CourseModule.query.filter_by(id=module_id).first()
        if not m:
            return get_response("Module not found", None, 404), 404
        data = lesson_create_parse.parse_args()
        l    = ModuleLesson(
            module_id   = module_id,
            title       = data["title"],
            order_num   = data.get("order_num") or 1,
            description = data.get("description"),
        )
        db.session.add(l)
        db.session.commit()
        return get_response("Lesson created", ModuleLesson.to_dict(l), 200), 200


class ModuleLessonResource(Resource):
    decorators = [role_required(["SUPERADMIN", "ADMIN"])]

    def get(self, module_id, lesson_id):
        l = ModuleLesson.query.filter_by(id=lesson_id, module_id=module_id).first()
        if not l:
            return get_response("Lesson not found", None, 404), 404
        return get_response("Lesson", ModuleLesson.to_dict(l), 200), 200

    def patch(self, module_id, lesson_id):
        l = ModuleLesson.query.filter_by(id=lesson_id, module_id=module_id).first()
        if not l:
            return get_response("Lesson not found", None, 404), 404
        data = lesson_update_parse.parse_args()
        if data.get("title"):       l.title       = data["title"]
        if data.get("order_num"):   l.order_num   = data["order_num"]
        if data.get("description") is not None: l.description = data["description"]
        db.session.commit()
        return get_response("Lesson updated", ModuleLesson.to_dict(l), 200), 200

    def delete(self, module_id, lesson_id):
        l = ModuleLesson.query.filter_by(id=lesson_id, module_id=module_id).first()
        if not l:
            return get_response("Lesson not found", None, 404), 404
        if l.file_path and os.path.exists(l.file_path):
            os.remove(l.file_path)
        db.session.delete(l)
        db.session.commit()
        return get_response("Lesson deleted", None, 200), 200


class ModuleLessonFileUploadResource(Resource):
    """POST /api/course-modules/<mid>/lessons/<lid>/upload — fayl yuklash"""
    decorators = [role_required(["SUPERADMIN", "ADMIN"])]

    def post(self, module_id, lesson_id):
        l = ModuleLesson.query.filter_by(id=lesson_id, module_id=module_id).first()
        if not l:
            return get_response("Lesson not found", None, 404), 404

        if "file" not in request.files:
            return get_response("'file' field required", None, 400), 400

        file = request.files["file"]
        if not file.filename:
            return get_response("No file selected", None, 400), 400
        if not allowed_file(file.filename):
            return get_response("Allowed: pdf, png, jpg, jpeg, webp", None, 400), 400

        # Eski faylni o'chirish
        if l.file_path and os.path.exists(l.file_path):
            os.remove(l.file_path)

        ext      = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        l.file_path = filepath
        l.file_name = file.filename
        l.file_type = get_file_type(file.filename)
        db.session.commit()

        return get_response("File uploaded", {
            **ModuleLesson.to_dict(l),
            "file_url": f"/uploads/{filename}",
        }, 200), 200

    def delete(self, module_id, lesson_id):
        """Faylni o'chirish"""
        l = ModuleLesson.query.filter_by(id=lesson_id, module_id=module_id).first()
        if not l:
            return get_response("Lesson not found", None, 404), 404
        if l.file_path and os.path.exists(l.file_path):
            os.remove(l.file_path)
        l.file_path = None
        l.file_name = None
        l.file_type = None
        db.session.commit()
        return get_response("File deleted", ModuleLesson.to_dict(l), 200), 200


# Public endpoint — fayl URL olish uchun (auth shart emas, URL orqali ko'rish)
class ModuleLessonFileViewResource(Resource):
    """GET /api/course-modules/<mid>/lessons/<lid>/file"""

    def get(self, module_id, lesson_id):
        l = ModuleLesson.query.filter_by(id=lesson_id, module_id=module_id).first()
        if not l or not l.file_path:
            return get_response("File not found", None, 404), 404
        filename = os.path.basename(l.file_path)
        return get_response("File info", {
            "file_url":  f"/uploads/{filename}",
            "file_name": l.file_name,
            "file_type": l.file_type,
        }, 200), 200


# ── REGISTER ──────────────────────────────────────────────────
api.add_resource(CourseModuleListResource,       "/")
api.add_resource(CourseModuleResource,           "/<int:module_id>")
api.add_resource(ModuleLessonListResource,       "/<int:module_id>/lessons")
api.add_resource(ModuleLessonResource,           "/<int:module_id>/lessons/<int:lesson_id>")
api.add_resource(ModuleLessonFileUploadResource, "/<int:module_id>/lessons/<int:lesson_id>/upload")
api.add_resource(ModuleLessonFileViewResource,   "/<int:module_id>/lessons/<int:lesson_id>/file")
