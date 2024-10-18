from pydantic import BaseModel


class LoginRequestDTO(BaseModel):

    reference_number: str
    email: str
    password: str
