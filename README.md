# CRM Backend — Flask-RESTful

Asl `crm-backend` loyihasining `myzone_online_rest` uslubida qayta yozilgan versiyasi.

## Arxitektura

```
crm_restful/
├── app.py                      # Asosiy Flask app
├── requirements.txt
├── models/
│   ├── __init__.py             # db, bcrypt, migrate
│   ├── user.py
│   ├── course.py
│   ├── group.py
│   ├── teacher.py
│   ├── lead.py
│   ├── student.py
│   ├── enrollment.py
│   ├── lesson.py
│   ├── attendance.py
│   ├── payment.py              # Payment + Debt
│   └── expense.py
├── routes/
│   ├── auth_route.py           # /api/auth/login, /api/auth/me
│   ├── admin_route.py          # /api/admin/users
│   ├── course_route.py         # /api/courses
│   ├── group_route.py          # /api/groups
│   ├── teacher_route.py        # /api/teachers + /api/groups salary
│   ├── operator_route.py       # /api/operator (leads, students, enrollments, payments)
│   ├── manager_route.py        # /api/manager (attendance, lessons, payment summary)
│   ├── lesson_route.py         # /api/lessons (cancel, move, restore)
│   └── expense_route.py        # /api/expenses
└── utils/
    ├── utils.py                # get_response(), create_admin()
    ├── decorators.py           # role_required()
    ├── lesson_generator.py     # generate_lessons_for_group()
    └── reschedule_helper.py    # cancel_and_reschedule()
```

## Kodlash uslubi (namuna: myzone_online_rest)

- `Blueprint` + `Api(blueprint)` pattern
- Har bir endpoint `Resource` class ichida (`get`, `post`, `patch`, `delete`)
- `reqparse.RequestParser()` — fayl boshida alohida
- Swagger docstring har bir methodda (`---` yaml formatida)
- `@role_required([...])` decorator — method ustida yoki `decorators = [...]`
- `get_response(message, result, status_code)` — barcha javoblar
- `Model.to_dict()` — `@staticmethod`, `_` o'zgaruvchi nomida
- `api.add_resource(...)` — fayl oxirida

## Endpoints

| Method | Path | Roles |
|--------|------|-------|
| POST | /api/auth/login | — |
| GET | /api/auth/me | ADMIN, MANAGER, OPERATOR |
| GET/POST | /api/admin/users | ADMIN |
| GET/PATCH/DELETE | /api/admin/users/<id> | ADMIN |
| GET/POST | /api/courses | ADMIN, MANAGER, OPERATOR |
| GET/PATCH/DELETE | /api/courses/<id> | ADMIN/all |
| GET/POST | /api/groups | ADMIN/all |
| GET/PATCH/DELETE | /api/groups/<id> | ADMIN/all |
| GET | /api/groups/<id>/info | ADMIN, MANAGER, OPERATOR |
| POST | /api/groups/<id>/generate-lessons | ADMIN |
| GET | /api/groups/<id>/salary-report | ADMIN, MANAGER |
| GET | /api/groups/<id>/salary-live | ADMIN, MANAGER |
| GET/POST | /api/teachers | ADMIN, MANAGER |
| GET/PATCH/DELETE | /api/teachers/<id> | ADMIN/MANAGER |
| GET | /api/teachers/<id>/salary-report | ADMIN, MANAGER |
| POST | /api/teachers/salary-calculate | ADMIN, MANAGER |
| GET/POST | /api/operator/leads | ADMIN, OPERATOR |
| GET/PATCH/DELETE | /api/operator/leads/<id> | ADMIN, OPERATOR |
| GET | /api/operator/leads/stats | ADMIN, OPERATOR |
| GET/POST | /api/operator/students | ADMIN, OPERATOR, MANAGER |
| GET/PATCH/DELETE | /api/operator/students/<id> | ADMIN, OPERATOR |
| GET/POST | /api/operator/enrollments | ADMIN, OPERATOR |
| PATCH/DELETE | /api/operator/enrollments/<id> | ADMIN, OPERATOR |
| GET/POST | /api/operator/payments | ADMIN, OPERATOR, MANAGER |
| GET/DELETE | /api/operator/payments/<id> | ADMIN, MANAGER |
| GET | /api/operator/debts/student/<id> | ADMIN, OPERATOR, MANAGER |
| GET | /api/manager/groups | ADMIN, MANAGER, OPERATOR |
| GET | /api/manager/groups/<id>/students | ADMIN, MANAGER, OPERATOR |
| GET | /api/manager/groups/<id>/lessons | ADMIN, MANAGER, OPERATOR |
| GET/POST | /api/manager/attendance | ADMIN, MANAGER, OPERATOR |
| PATCH/DELETE | /api/manager/attendance/<id> | ADMIN, MANAGER, OPERATOR |
| GET | /api/manager/lessons | ADMIN, MANAGER |
| GET | /api/manager/lessons/<id> | ADMIN, MANAGER |
| GET | /api/manager/payments/student/<id> | ADMIN, MANAGER |
| GET | /api/manager/payments/summary | ADMIN, MANAGER |
| POST | /api/lessons/cancel | ADMIN, MANAGER |
| GET | /api/lessons/group/<id> | ADMIN, MANAGER, OPERATOR |
| PATCH | /api/lessons/<id>/restore | ADMIN, MANAGER |
| PATCH | /api/lessons/<id>/move | ADMIN, MANAGER |
| GET/POST | /api/expenses | ADMIN, MANAGER |
| DELETE | /api/expenses/<id> | ADMIN |
| GET | /api/expenses/summary | ADMIN, MANAGER |
| GET | /health | — |
