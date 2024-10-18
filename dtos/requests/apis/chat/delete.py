from typing import Optional
from dtos.requests.apis.base import BaseRequestDTO


class DeleteChatRequestDTO(BaseRequestDTO):
    
    chat_urn: str