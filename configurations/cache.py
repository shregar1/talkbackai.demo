import json
#
from dtos.configurations.cache import CacheConfigurationDTO
#
from start_utils import logger


class CacheConfiguration:
    _instance = None

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super(CacheConfiguration, cls).__new__(cls)
            cls._instance.config = {}
            cls._instance.load_config()
        return cls._instance

    def load_config(self):

        try:

            with open('configs/cache/config.json', 'r') as file:
                self.config = json.load(file)

        except FileNotFoundError:
            logger.debug('Config file not found.')

        except json.JSONDecodeError:
            logger.debug('Error decoding config file.')

    def get_config(self):
        return CacheConfigurationDTO(
            host=self.config.get("host", "redis"),
            port=self.config.get("port", 6379),
            password=self.config.get("password", None)
        )