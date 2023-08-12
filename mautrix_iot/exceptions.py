from mautrix_iot.consts import MatrixErrorCode


class MatrixError(Exception):
    def __init__(self):
        self.m_code: MatrixErrorCode = MatrixErrorCode.M_UNKNOWN
        self.msg: str = "An error has occured"


class UnauthorizedError(MatrixError):
    def __init__(self):
        self.m_code = MatrixErrorCode.M_MISSING_TOKEN
        self.msg = "Authorization header was not provided"


class ForbiddenError(MatrixError):
    def __init__(self):
        self.m_code = MatrixErrorCode.M_FORBIDDEN
        self.msg = "Authorization header is invalid"


class InvalidUsernameError(MatrixError):
    def __init__(self, expected_username):
        self.m_code = MatrixErrorCode.M_INVALID_USERNAME
        self.msg = f"Expected event for {expected_username}"


class BadJsonError(MatrixError):
    def __init__(self):
        self.m_code = MatrixErrorCode.M_BAD_JSON
        self.msg = f"Missing keys from JSON"


class RateLimitedError(MatrixError):
    def __init__(self):
        self.m_code = MatrixErrorCode.M_LIMIT_EXCEEDED
        self.msg = f"Too many requests"
