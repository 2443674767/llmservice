
class AdminException(Exception):
    def __init__(self, message, code=400):
        super().__init__(message)
        self.type = "admin"
        self.code = code
        self.message = message


class UserNotFoundError(AdminException):
    def __init__(self, username):
        super().__init__(f"User '{username}' not found", 404)
        