class APIError(Exception):
    def __init__(self, status_code: int, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.code = code or status_code
