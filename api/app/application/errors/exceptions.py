from typing import Any


class AppException(RuntimeError):
    """基础应用异常类，继承 RuntimeError"""

    def __init__(self,
        code: int = 400, # 自定义业务错误码,
        status_code: int = 400,
        msg: str = "应用发生异常，请稍后重试",
        data: Any = None,
    ):
        self.code = code
        self.status_code = status_code
        self.msg = msg
        self.data = data
        super().__init__()

class BadRequestError(AppException):
    """客户端请求错误"""

    def __init__(self, msg: str = "客户端请求错误，请检查后重试"):
        super().__init__(status_code=400, code=400, msg=msg)

class NotFoundError(AppException):
    """资源未找到错误"""

    def __init__(self, msg: str = "资源未找到，请核实后重试"):
        super().__init__(status_code=404, code=404, msg=msg)

class ValidationError(AppException):
    """数据校验错误"""

    def __init__(self, msg: str = "请求参数校验错误，请核实后重试"):
        super().__init__(status_code=422, code=422, msg=msg)

class TooManyRequestError(AppException):
    """请求过多错误，触发限流"""

    def __init__(self, msg: str = "请求过多，触发限流，请稍后重试"):
        super().__init__(status_code=429, code=429, msg=msg)

class ServerError(AppException):
    """服务器异常错误"""

    def __init__(self, msg: str = "服务器出现异常，请稍后重试"):
        super().__init__(status_code=500, code=500, msg=msg)