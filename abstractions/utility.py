from abc import ABC
from loguru import logger


class IUtility(ABC):

    def __init__(self, urn: str = None) -> None:
        
        super().__init__()
        self.urn = urn
        self.logger = logger.bind(urn=self.urn)