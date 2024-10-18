from dataclasses import dataclass

@dataclass
class DBConfigurationDTO:
    user_name: str
    password: str
    host: str
    port: int
    database: str
