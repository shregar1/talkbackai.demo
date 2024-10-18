import base64

from abstractions.utility import IUtility


class Base64Utility(IUtility):

    def __init__(self, urn: str = None) -> None:
        super().__init__(urn)
        self.urn = urn

    async def base64_to_bytes(self, base64_string: str):

        self.logger.debug("Converting base64 string to bytes")
        byte_data = base64.b64decode(base64_string)
        self.logger.debug("Converted base64 string to bytes")

        return byte_data
    
    async def bytes_to_base64(self, byte_data: bytes):

        self.logger.debug("Converting bytes to base64 string")
        base64_string = base64.b64encode(byte_data).decode('utf-8')
        self.logger.debug("Converted bytes to base64 string")

        return base64_string
