from pydantic import BaseModel


class LogoutRequestDTO(BaseModel):

    reference_number: str
