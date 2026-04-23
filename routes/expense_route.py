from datetime       import date
from flask          import Blueprint, request
from flask_restful  import Api, Resource, reqparse
from flask_jwt_extended import get_jwt_identity
from sqlalchemy     import func

from models             import db
from models.expense     import Expense
from models.payment     import Payment
from utils.utils        import get_response
from utils.decorators   import role_required

VALID_CATEGORIES = {"ijara", "maosh", "jihozlar", "kommunal", "marketing", "boshqa"}

# ============================================================
# PARSERS
# ============================================================
expense_create_parse = reqparse.RequestParser()
expense_create_parse.add_argument("amount",       type=float, required=True, help="Amount cannot be blank")
expense_create_parse.add_argument("description",  type=str,   required=True, help="Description cannot be blank")
expense_create_parse.add_argument("category",     type=str,   default="boshqa")
expense_create_parse.add_argument("expense_date", type=str)

# ============================================================
# BLUEPRINT + API
# ============================================================
expense_bp = Blueprint("expense", __name__, url_prefix="/api/expenses")
api        = Api(expense_bp)


# ============================================================
# RESOURCES
# ============================================================
class ExpenseResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def delete(self, expense_id):
        """Expense Delete API
        Path   - /api/expenses/<expense_id>
        Method - DELETE
        ---
        consumes: application/json
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
              description: Bearer token for authentication
            - name: expense_id
              in: path
              type: integer
              required: true
              description: Enter Expense ID
        responses:
            200:
                description: Expense successfully deleted
            404:
                description: Expense not found
        """
        expense = Expense.query.filter_by(id=expense_id).first()
        if not expense:
            return get_response("Expense not found", None, 404), 404

        db.session.delete(expense)
        db.session.commit()
        return get_response("Expense successfully deleted", None, 200), 200


class ExpenseListCreateResource(Resource):

    @role_required(["SUPERADMIN", "ADMIN"])
    def get(self):
        """Expense List API
        Path   - /api/expenses
        Method - GET
        ---
        consumes: application/json
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
              description: Bearer token for authentication
            - name: from
              in: query
              type: string
              description: Filter from date (YYYY-MM-DD)
            - name: to
              in: query
              type: string
              description: Filter to date (YYYY-MM-DD)
        responses:
            200:
                description: Return Expense List
        """
        from_date = request.args.get("from")
        to_date   = request.args.get("to")
        query     = Expense.query

        if from_date:
            try:
                query = query.filter(Expense.expense_date >= date.fromisoformat(from_date))
            except ValueError:
                pass
        if to_date:
            try:
                query = query.filter(Expense.expense_date <= date.fromisoformat(to_date))
            except ValueError:
                pass

        expenses = query.order_by(Expense.expense_date.desc()).all()
        result   = [Expense.to_dict(e) for e in expenses]
        return get_response("Expense List", result, 200), 200

    @role_required(["SUPERADMIN", "ADMIN"])
    def post(self):
        """Expense Create API
        Path   - /api/expenses
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
                    amount:
                        type: number
                    description:
                        type: string
                    category:
                        type: string
                    expense_date:
                        type: string
                required: [amount, description]
        responses:
            200:
                description: Expense successfully created
            400:
                description: amount or description missing, or invalid date format
        """
        user_id          = int(get_jwt_identity())
        data             = expense_create_parse.parse_args()
        amount           = data["amount"]
        description      = data["description"]
        category         = (data.get("category") or "boshqa").lower()
        expense_date_str = data.get("expense_date")

        try:
            exp_date = date.fromisoformat(expense_date_str) if expense_date_str else date.today()
        except ValueError:
            return get_response("Invalid date format. Use YYYY-MM-DD", None, 400), 400

        new_expense = Expense(
            amount       = amount,
            description  = description,
            category     = category,
            expense_date = exp_date,
            created_by   = user_id,
        )
        db.session.add(new_expense)
        db.session.commit()
        return get_response("Expense successfully created", Expense.to_dict(new_expense), 200), 200


class ExpenseSummaryResource(Resource):
    decorators = [role_required(["SUPERADMIN", "ADMIN"])]

    def get(self):
        """Expense Summary API
        Path   - /api/expenses/summary
        Method - GET
        ---
        consumes: application/json
        parameters:
            - in: header
              name: Authorization
              type: string
              required: true
              description: Bearer token for authentication
            - name: from
              in: query
              type: string
              description: Filter from date (YYYY-MM-DD)
            - name: to
              in: query
              type: string
              description: Filter to date (YYYY-MM-DD)
        responses:
            200:
                description: Return financial summary (income, expenses, net profit)
        """
        from_date = request.args.get("from")
        to_date   = request.args.get("to")

        pay_query = db.session.query(func.sum(Payment.amount).label("total"))
        exp_query = Expense.query

        if from_date:
            try:
                fd = date.fromisoformat(from_date)
                pay_query = pay_query.filter(Payment.payment_date >= fd)
                exp_query = exp_query.filter(Expense.expense_date >= fd)
            except ValueError:
                pass
        if to_date:
            try:
                td = date.fromisoformat(to_date)
                pay_query = pay_query.filter(Payment.payment_date <= td)
                exp_query = exp_query.filter(Expense.expense_date <= td)
            except ValueError:
                pass

        total_income  = float(pay_query.scalar() or 0)
        expenses      = exp_query.all()
        total_expense = sum(e.amount for e in expenses)
        net_profit    = total_income - total_expense

        by_category = {}
        for e in expenses:
            cat = e.category or "boshqa"
            by_category[cat] = by_category.get(cat, 0) + e.amount

        result = {
            "total_income":  total_income,
            "total_expense": total_expense,
            "net_profit":    net_profit,
            "by_category":   by_category,
            "expense_count": len(expenses),
        }
        return get_response("Financial summary", result, 200), 200


# ============================================================
# REGISTER RESOURCES
# ============================================================
api.add_resource(ExpenseListCreateResource, "/")
api.add_resource(ExpenseResource,           "/<int:expense_id>")
api.add_resource(ExpenseSummaryResource,    "/summary")