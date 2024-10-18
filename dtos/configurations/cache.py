from dataclasses import dataclass


@dataclass
class CacheConfigurationDTO:

    host: str
    port: int
    password: str