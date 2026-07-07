class MangagraphError(Exception):
    pass

class InvalidURLException(MangagraphError):
    def __init__(self, url, message="Invalid URL provided."):
        self.url = url
        self.message = message
        super().__init__(f"{self.message} URL: {self.url}")

class RequestFailedException(MangagraphError):
    def __init__(self, url, message="Request to the URL failed."):
        self.url = url
        self.message = message
        super().__init__(f"{self.message} URL: {self.url}")

class TelegraphError(MangagraphError):
    def __init__(self, method, message):
        self.method = method
        self.message = message
        super().__init__(f"Telegraph {method}: {message}")