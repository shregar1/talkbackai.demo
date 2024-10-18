from abc import ABC
from ulid import ulid

from start_utils import logger


class IEvent(ABC):
    urn = ulid()
    logger = logger

    @classmethod
    def configure(cls, urn: str):
        cls.urn = urn
        cls.logger = cls.logger.bind(urn=cls.urn)

        