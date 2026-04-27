"""
Kurs modullari va modul darslarini boshqarish.
Fayl yuklash: base64 formatida PostgreSQL'da saqlanadi — Vercel-compatible.
"""
import base64
from flask          import Blueprint, request, make_response
from flask_restful  import Api, Resource, reqparse

from models                  import db
from models.course           import Course
from models.course_module    import CourseModule, ModuleLesson
from utils.utils             import get_response
from utils.decorators        import role_required

ALLOWED_EXT  = {"pdf", "png", "jpg", "jpeg", "webp"}
MAX_SIZE     = 20 * 1024 * 1024   # 20 MB

MIME_MAP = {
    "pdf":  "application/pdf",
    "png":  "image/png",
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def get_file_type(filename):
    ext = filename.rsplit(".", 1)[1].lower()
    return "pdf" if ext == "pdf" else "image"

def get_ext(filename):
    return filename.rsplit(".", 1)[-1].lower() if filename and "." in filename else "bin"

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


# ── MODULLAR ─────────────────────────────────────────────────
class CourseModuleListResource(Resource):
    decorators = [role_required(["SUPERADMIN", "ADMIN"])]

    def get(self):
        course_id = request.args.get("course_id", type=int)
        q = CourseModule.query
        if course_id:
            q = q.filter_by(course_id=course_id)
        modules = q.order_by(CourseModule.order_num).all()
        return get_response("Modules", [CourseModule.to_dict(m, include_lessons=True) for m in modules], 200), 200

    def post(self):
        course_id = request.args.get("course_id", type=int)
        if not course_id:
            return get_response("course_id required", None, 400), 400
        if not Course.query.filter_by(id=course_id).first():
            return get_response("Course not found", None, 404), 404
        data = module_create_parse.parse_args()
        m = CourseModule(
            course_id=course_id, title=data["title"],
            order_num=data.get("order_num") or 1, description=data.get("description"),
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
        if data.get("title"):     m.title     = data["title"]
        if data.get("order_num"): m.order_num = data["order_num"]
        if data.get("description") is not None: m.description = data["description"]
        db.session.commit()
        return get_response("Module updated", CourseModule.to_dict(m, include_lessons=True), 200), 200

    def delete(self, module_id):
        m = CourseModule.query.filter_by(id=module_id).first()
        if not m:
            return get_response("Module not found", None, 404), 404
        db.session.delete(m)
        db.session.commit()
        return get_response("Module deleted", None, 200), 200


# ── DARSLAR ──────────────────────────────────────────────────
class ModuleLessonListResource(Resource):
    decorators = [role_required(["SUPERADMIN", "ADMIN"])]

    def get(self, module_id):
        m = CourseModule.query.filter_by(id=module_id).first()
        if not m:
            return get_response("Module not found", None, 404), 404
        return get_response("Lessons", [ModuleLesson.to_dict(l) for l in m.lessons.all()], 200), 200

    def post(self, module_id):
        m = CourseModule.query.filter_by(id=module_id).first()
        if not m:
            return get_response("Module not found", None, 404), 404
        data = lesson_create_parse.parse_args()
        l = ModuleLesson(
            module_id=module_id, title=data["title"],
            order_num=data.get("order_num") or 1, description=data.get("description"),
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
        if data.get("title"):     l.title     = data["title"]
        if data.get("order_num"): l.order_num = data["order_num"]
        if data.get("description") is not None: l.description = data["description"]
        db.session.commit()
        return get_response("Lesson updated", ModuleLesson.to_dict(l), 200), 200

    def delete(self, module_id, lesson_id):
        l = ModuleLesson.query.filter_by(id=lesson_id, module_id=module_id).first()
        if not l:
            return get_response("Lesson not found", None, 404), 404
        db.session.delete(l)
        db.session.commit()
        return get_response("Lesson deleted", None, 200), 200


# ── FAYL YUKLASH ─────────────────────────────────────────────
class ModuleLessonFileUploadResource(Resource):
    """POST   /api/course-modules/<mid>/lessons/<lid>/upload — fayl yuklash
       DELETE /api/course-modules/<mid>/lessons/<lid>/upload — faylni o'chirish
    """
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

        file_bytes = file.read()
        if len(file_bytes) > MAX_SIZE:
            return get_response("File too large. Max 20MB", None, 400), 400

        l.file_data = base64.b64encode(file_bytes).decode("utf-8")
        l.file_name = file.filename
        l.file_type = get_file_type(file.filename)
        l.file_size = len(file_bytes)
        db.session.commit()

        return get_response("File uploaded", ModuleLesson.to_dict(l), 200), 200

    def delete(self, module_id, lesson_id):
        l = ModuleLesson.query.filter_by(id=lesson_id, module_id=module_id).first()
        if not l:
            return get_response("Lesson not found", None, 404), 404
        l.file_data = None
        l.file_name = None
        l.file_type = None
        l.file_size = None
        db.session.commit()
        return get_response("File deleted", ModuleLesson.to_dict(l), 200), 200


# ── FAYL KO'RISH ─────────────────────────────────────────────
class ModuleLessonFileViewResource(Resource):
    """GET /api/course-modules/<mid>/lessons/<lid>/file
    
    Faylni to'g'ridan-to'g'ri browser'da ochadi (PDF, rasm).
    send_file ishlatmaydi — Vercel bilan muammosiz ishlaydi.
    """

    def get(self, module_id, lesson_id):
        l = ModuleLesson.query.filter_by(id=lesson_id, module_id=module_id).first()
        if not l:
            return get_response("Lesson not found", None, 404), 404
        if not l.file_data:
            return get_response("Bu darsda fayl yo'q", None, 404), 404

        try:
            file_bytes = base64.b64decode(l.file_data)
        except Exception:
            return get_response("Fayl buzilgan", None, 500), 500

        ext  = get_ext(l.file_name)
        mime = MIME_MAP.get(ext, "application/octet-stream")

        response = make_response(file_bytes)
        response.headers["Content-Type"]        = mime
        response.headers["Content-Disposition"] = f'inline; filename="{l.file_name or "file"}"'
        response.headers["Content-Length"]      = len(file_bytes)
        response.headers["Cache-Control"]       = "public, max-age=3600"
        return response


class ModuleLessonFileInfoResource(Resource):
    """GET /api/course-modules/<mid>/lessons/<lid>/file-info
    
    Fayl haqida ma'lumot + base64 data qaytaradi.
    Frontend PDF.js yoki <img> tag bilan ko'rsatish uchun.
    """
    decorators = [role_required(["SUPERADMIN", "ADMIN"])]

    def get(self, module_id, lesson_id):
        l = ModuleLesson.query.filter_by(id=lesson_id, module_id=module_id).first()
        if not l:
            return get_response("Lesson not found", None, 404), 404
        if not l.file_data:
            return get_response("Bu darsda fayl yo'q", None, 404), 404

        ext  = get_ext(l.file_name)
        mime = MIME_MAP.get(ext, "application/octet-stream")

        return get_response("File info", {
            "file_name":   l.file_name,
            "file_type":   l.file_type,
            "file_size":   l.file_size,
            "mime_type":   mime,
            # Frontend uchun to'liq data URL — <img src="..."> yoki PDF.js ga bera olasiz
            "data_url":    f"data:{mime};base64,{l.file_data}",
            "file_data":   l.file_data,
        }, 200), 200


# ── REGISTER ──────────────────────────────────────────────────
api.add_resource(CourseModuleListResource,       "/")
api.add_resource(CourseModuleResource,           "/<int:module_id>")
api.add_resource(ModuleLessonListResource,       "/<int:module_id>/lessons")
api.add_resource(ModuleLessonResource,           "/<int:module_id>/lessons/<int:lesson_id>")
api.add_resource(ModuleLessonFileUploadResource, "/<int:module_id>/lessons/<int:lesson_id>/upload")
api.add_resource(ModuleLessonFileViewResource,   "/<int:module_id>/lessons/<int:lesson_id>/file")
api.add_resource(ModuleLessonFileInfoResource,   "/<int:module_id>/lessons/<int:lesson_id>/file-info")
