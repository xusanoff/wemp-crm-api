import os
import logging
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from flask_jwt_extended import JWTManager
from sshtunnel import SSHTunnelForwarder

from models import db, bcrypt, migrate

from routes.auth_route          import auth_bp
from routes.admin_route         import admin_bp
from routes.course_route        import course_bp
from routes.course_module_route import course_module_bp, file_bp
from routes.operator_route      import operator_bp
from routes.manager_route       import manager_bp
from routes.lesson_route        import lesson_bp
from routes.expense_route       import expense_bp

# ── SSH TUNNEL ────────────────────────────────────────────────────
tunnel = SSHTunnelForwarder(
    ('185.180.231.43', 22),
    ssh_username='root',
    ssh_password='TCjTvI6Y02VM',
    remote_bind_address=('127.0.0.1', 5432)
)
tunnel.start()

DB_URL = f"postgresql://akbarov:akbarov@127.0.0.1:{tunnel.local_bind_port}/wemp_crm_db"


# ── APP FACTORY ───────────────────────────────────────────────────
def create_app():
    app = Flask(__name__)

    # ── CORS ──────────────────────────────────────────────────────
    CORS(app,
         origins=["https://wemp-crm.vercel.app"],
         methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"],
         supports_credentials=True)

    # ── CONFIG ────────────────────────────────────────────────────
    app.config["DEBUG"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dhq34155kjnjhjbu723uy545")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dfgsk43jkh3kj4jhv23jdfw4jkh34kjh")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 10800
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"] = False
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

    # ── EXTENSIONS ────────────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    JWTManager(app)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")

    Swagger(app, template={"info": {"title": "CRM Backend API", "version": "3.0.0"}})

    # ── BLUEPRINTS ────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(course_bp)
    app.register_blueprint(course_module_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(operator_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(lesson_bp)
    app.register_blueprint(expense_bp)

    # ── DB INIT ───────────────────────────────────────────────────
    with app.app_context():
        from models.user          import User          # noqa
        from models.course        import Course        # noqa
        from models.course_module import CourseModule, ModuleLesson  # noqa
        from models.group         import Group         # noqa
        from models.lesson        import Lesson        # noqa
        from models.student       import Student       # noqa
        from models.enrollment    import Enrollment    # noqa
        from models.attendance    import Attendance    # noqa
        from models.payment       import Payment, Debt # noqa
        from models.expense       import Expense       # noqa
        from models.monthly_debt  import MonthlyDebt   # noqa

        db.create_all()

        from utils.utils import create_admin
        create_admin()

    # ── BOT SCHEDULER ─────────────────────────────────────────────
    try:
        from bot.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        print(f"[BOT] Scheduler start error: {e}")

    # ── ROUTES ────────────────────────────────────────────────────
    @app.route("/")
    def home():
        return {"message": "CRM Backend API", "docs": "/apidocs"}, 200

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "crm-backend", "version": "3.0.0"}, 200

    return app


# ── Vercel bu qatorni qidiradi ────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
