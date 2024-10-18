import re
#
from loguru import logger
from typing import List
#
from abstractions.utility import IUtility

class DictionaryUtility(IUtility):

    def __init__(self, urn: str = None) -> None:
        super().__init__(urn)
        self.urn = urn
        self.logger = logger

    def build_dictonary_with_key(self, records: List, key: str):

        result: dict = dict()

        for record in records:
            result[getattr(record, key)] = record

        return result
    
    def snake_to_camel_case(self, snake_str):
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    def convert_dict_keys_to_camel_case(self, data):
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                new_key = self.snake_to_camel_case(k)
                new_dict[new_key] = self.convert_dict_keys_to_camel_case(v)
            return new_dict
        elif isinstance(data, list):
            return [self.convert_dict_keys_to_camel_case(item) for item in data]
        else:
            return data
        
    def camel_to_snake_case(self, name: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def convert_dict_keys_to_snake_case(self, data: dict):

        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                new_key = self.camel_to_snake_case(k)
                new_dict[new_key] = self.convert_dict_keys_to_snake_case(v)
            return new_dict

        elif isinstance(data, list):

            return [self.convert_dict_keys_to_snake_case(item) for item in data]

        else:
            return data
        
    def mask_value(self, value):
        # Example masking function: replace each character with 'X'
        if isinstance(value, str):
            return 'X' * len(value)
        elif isinstance(value, int):
            return 0
        elif isinstance(value, float):
            return 0.0
        return value

    def mask_dict_values(self, data):
        if isinstance(data, dict):
            return {k: self.mask_dict_values(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.mask_dict_values(item) for item in data]
        else:
            return self.mask_value(data)
        
    def remove_keys_from_dict(self, data: dict, keys_to_remove: List[str]) -> dict:
        """
        Remove specified keys from a dictionary recursively.
        
        :param d: Dictionary from which keys need to be removed.
        :param keys_to_remove: Set of keys to remove.
        :return: Dictionary with specified keys removed.
        """
        if isinstance(data, dict):
            return {k: self.remove_keys_from_dict(v, keys_to_remove) for k, v in data.items() if k not in keys_to_remove}
        elif isinstance(data, list):
            return [self.remove_keys_from_dict(i, keys_to_remove) for i in data]
        else:
            return data