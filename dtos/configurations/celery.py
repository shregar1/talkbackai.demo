from dataclasses import dataclass


@dataclass
class CeleryConfigurationDTO:

    backend_url: str
    broker_url: str
    db: int