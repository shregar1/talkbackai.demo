from pydantic import BaseModel


class RegisterRequestDTO(BaseModel):

    reference_number: str
    email: str
    password: str
