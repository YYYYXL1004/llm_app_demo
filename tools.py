import ast
import json
import operator
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


# 这份 schema 会直接传给模型，告诉模型“有哪些工具、每个工具需要什么参数”。
# 注意：schema 只是说明书，真正执行工具的是下面的 Python 函数。
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "查询指定时区的当前时间。",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA 时区名称，例如 Asia/Shanghai 或 America/New_York。",
                    }
                },
                "required": ["timezone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "执行安全的四则运算，适合精确计算。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "只包含数字、括号和 + - * / ** % 的表达式。",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "python_function_status",
            "description": "示例：查询某个已有 Python 函数的 Tool Calling 接入状态。",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "已有 Python 函数名，例如 search_api、crawler、database_query。",
                    }
                },
                "required": ["tool_name"],
            },
        },
    },
]

# 计算器只允许这些 AST 运算节点，避免 eval 执行任意代码。
ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
ALLOWED_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def safe_eval_math(expression: str) -> float | int:
    """安全计算简单数学表达式，不允许函数调用、变量名或属性访问。"""
    if len(expression) > 100:
        raise ValueError("表达式过长")

    tree = ast.parse(expression, mode="eval")

    def eval_node(node):
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BIN_OPS:
            left = eval_node(node.left)
            right = eval_node(node.right)
            return ALLOWED_BIN_OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_UNARY_OPS:
            return ALLOWED_UNARY_OPS[type(node.op)](eval_node(node.operand))
        raise ValueError("只允许数字和基本数学运算")

    return eval_node(tree)


def get_current_time(timezone: str = "Asia/Shanghai") -> dict[str, Any]:
    """工具函数：返回指定时区的当前时间。"""
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        timezone = "Asia/Shanghai"
        tz = ZoneInfo(timezone)

    now = datetime.now(tz)
    return {
        "timezone": timezone,
        "datetime": now.isoformat(timespec="seconds"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
    }


def calculator(expression: str) -> dict[str, Any]:
    """工具函数：计算四则运算表达式。"""
    value = safe_eval_math(expression)
    return {"expression": expression, "result": value}


def python_function_status(tool_name: str) -> dict[str, Any]:
    """工具函数：演示如何把已有 Python 函数包装成 Tool Calling 工具。"""
    examples = {
        "search_api": "已封装为函数：输入 query，输出结构化搜索结果。",
        "crawler": "已封装为函数：输入 url，输出正文、标题和来源。",
        "database_query": "已封装为函数：输入查询条件，输出表格记录。",
    }
    return {
        "tool_name": tool_name,
        "status": examples.get(tool_name, "未登记。课堂上可以把任意 Python 函数按同样方式包装成 tool。"),
        "next_step": "为该函数补充 JSON Schema，并在 tools 列表中注册。",
    }


def run_tool(name: str, arguments: dict[str, Any]) -> str:
    """根据模型返回的工具名和参数，分发到真正的 Python 函数。"""
    if name == "get_current_time":
        result = get_current_time(arguments.get("timezone", "Asia/Shanghai"))
    elif name == "calculator":
        result = calculator(arguments["expression"])
    elif name == "python_function_status":
        result = python_function_status(arguments["tool_name"])
    else:
        result = {"error": f"未知工具：{name}"}

    # tool message 的 content 必须是字符串，所以这里把 dict 转成 JSON 字符串。
    return json.dumps(result, ensure_ascii=False)