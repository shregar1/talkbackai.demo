from pydantic import BaseModel


class OnlineUsersRequestDTO(BaseModel):

    reference_number: str
