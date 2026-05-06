from models import db


class Course(db.Model):
    __tablename__ = "courses"

    id               = db.Column(db.Integer, primary_key=True)
    name             = db.Column(db.String(100), nullable=False)
    price            = db.Column(db.Float, nullable=False)
    duration_months  = db.Column(db.Integer, nullable=False, default=1)

    # Course o'chirilsa => groups va modules ham o'chadi
    groups  = db.relationship("Group",        backref="course_ref",   lazy="dynamic",
                               cascade="all, delete-orphan")
    modules = db.relationship("CourseModule", backref="course_ref",   lazy="dynamic",
                               cascade="all, delete-orphan")

    def __init__(self, name, price, duration_months=1):
        super().__init__()
        self.name            = name
        self.price           = price
        self.duration_months = duration_months

    @property
    def total_price(self):
        return self.price * self.duration_months

    @staticmethod
    def to_dict(course):
        _ = {
            "id":              course.id,
            "name":            course.name,
            "price":           course.price,
            "duration_months": course.duration_months,
            "total_price":     course.price * course.duration_months,
        }
        return _
