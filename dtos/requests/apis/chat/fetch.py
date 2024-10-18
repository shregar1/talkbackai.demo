from typing import Optional
from dtos.requests.apis.base import BaseRequestDTO


class FetchChatRequestDTO(BaseRequestDTO):
    
    chat_type: Optional[str] = None