from pydantic import BaseModel


class AuthenticateRequestDTO(BaseModel):

    reference_number: str
    token: str
