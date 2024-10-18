from dtos.requests.apis.base import BaseRequestDTO


class BuildRAGRequestDTO(BaseRequestDTO):
    
    document_file_path: str