from abstractions.error import IError


class UnexpectedResponseError(IError):

    def __init__(self, response_message: str, response_key: str, http_status_code: int) -> None:

        super().__init__()
        self.response_message = response_message
        self.response_key = response_key
        self.http_status_code = http_status_code