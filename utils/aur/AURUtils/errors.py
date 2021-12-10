class RPCError(Exception):

    def __init__(self, method: str, message: str):
        self.method = method
        self.message = message

    def __str__(self):
        return f'Method({self.method}): {self.message}'


class PackageNotFound(Exception):
    pass


class MaxRetries(Exception):
    pass
