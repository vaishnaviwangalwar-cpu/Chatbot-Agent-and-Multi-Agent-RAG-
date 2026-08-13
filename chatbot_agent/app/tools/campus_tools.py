import ast
import datetime
import operator
from typing import Callable, List

from app.prompts import CAMPUS_FAQS


def get_current_datetime() -> str:
    """
    Returns the current day, date, and time.
    Call this tool whenever the student asks what day, date, or time it currently is.
    """
    now = datetime.datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M %p")


def calculate(expression: str) -> str:
    """
    Safely evaluates a basic mathematical expression (addition, subtraction, multiplication, division, exponentiation).
    Call this tool whenever a math calculation or percentage calculation is required.

    Args:
        expression: A math string like "340 / 8", "1500 * 0.15", or "12 + 45 * 2".
    """
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp):  # <left> <op> <right>
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type in allowed_operators:
                return allowed_operators[op_type](left, right)
            raise ValueError(f"Unsupported operator: {op_type}")
        elif isinstance(node, ast.UnaryOp):  # -<operand> or +<operand>
            operand = _eval(node.operand)
            op_type = type(node.op)
            if op_type in allowed_operators:
                return allowed_operators[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type}")
        else:
            raise ValueError("Invalid mathematical expression structure.")

    try:
        clean_expr = expression.strip()
        parsed = ast.parse(clean_expr, mode="eval")
        val = _eval(parsed.body)
        return f"Calculation result for '{clean_expr}': {val}"
    except Exception as e:
        return f"Could not evaluate expression '{expression}': {str(e)}"


def lookup_faq(topic: str) -> str:
    """
    Searches the official DY Patil University FAQ knowledge base for information on campus facilities, fees, wifi, or schedules.

    Args:
        topic: The topic keyword to search for (e.g. "library hours", "hostel fees", "exam schedule", "wifi access", "campus shuttle").
    """
    query = topic.lower().strip()
    for key, answer in CAMPUS_FAQS.items():
        if key in query or query in key:
            return answer

    return f"No direct FAQ entry found for topic '{topic}'. Please contact the university helpdesk at helpdesk@dypatil.edu."


# List of Python tools exposed to the Gemini Client
CAMPUS_TOOLS: List[Callable] = [get_current_datetime, calculate, lookup_faq]
