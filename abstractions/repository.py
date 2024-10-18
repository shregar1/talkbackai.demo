from abc import ABC
from loguru import logger

class IRepository(ABC):

    def __init__(
        self, 
        urn: str = None, 
        user_urn: str = None, 
        api_name: str = None
    ) -> None:
        self.urn = urn
        self.user_urn = user_urn
        self.api_name = api_name
        self.logger = logger.bind(urn=self.urn, user_urn=self.user_urn, api_name=self.api_name)