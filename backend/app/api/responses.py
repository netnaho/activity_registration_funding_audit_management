from typing import Any


def success_response(data: Any = None, msg: str = "OK", code: int = 200) -> dict[str, Any]:
    return {"code": code, "msg": msg, "data": data}


def error_response(code: int, msg: str, data: Any = None) -> dict[str, Any]:
    return {"code": code, "msg": msg, "data": data}
