from pydantic import BaseModel


class BaseRequestDTO(BaseModel):

    reference_number: str