import json
#
from dtos.configurations.celery import CeleryConfigurationDTO
#
from start_utils import logger


class CeleryConfiguration:
    _instance = None

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super(CeleryConfiguration, cls).__new__(cls)
            cls._instance.config = {}
            cls._instance.load_config()
        return cls._instance

    def load_config(self):

        try:

            with open('config/celery/config.json', 'r') as file:
                self.config = json.load(file)

        except FileNotFoundError:
            logger.debug('Config file not found.')

        except json.JSONDecodeError:
            logger.debug('Error decoding config file.')

    def get_config(self):
        return CeleryConfigurationDTO(
            backend_url=self.config.get("backend_url", "redis://:{password}@{host}:{port}/{db}"),
            broker_url=self.config.get("broker_url", "redis://:{password}@{host}:{port}/{db}"),
            db=self.config.get("db", 0)
        )