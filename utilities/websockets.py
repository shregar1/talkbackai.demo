from fastapi import WebSocket
from typing_extensions import Dict, List, Union

from abstractions.utility import IUtility



class WebsocketUtility(IUtility):

    def __init__(self, urn: str = None) -> None:
        super().__init__(urn)
        self.urn = urn

    async def send_bytes(self, websocket: WebSocket, event_data: bytes) -> bool:

        try:

            self.logger.debug("Sending bytes data over websocket")
            await websocket.send_bytes(data=event_data)
            self.logger.debug('Sent bytes data over websocket')

            return True

        except Exception as err:

            self.logger.error(f"An error occured while send data over websocket: {err}")
            return False

    async def send_json(self, websocket: WebSocket, event_data: Union[List[str], Dict[str, str]]) -> bool:

        try:

            self.logger.debug("Sending json data over websocket")
            await websocket.send_json(data=event_data)
            self.logger.debug('Sent json data over websocket')

            return True

        except Exception as err:

            self.logger.error(f"An error occured while send data over websocket: {err}")
            return False
        
    async def send_text(self, websocket: WebSocket, event_data: str) -> bool:

        try:

            self.logger.debug("Sending text data over websocket")
            await websocket.send_text(data=event_data)
            self.logger.debug('Sent text data over websocket')

            return True

        except Exception as err:

            self.logger.error(f"An error occured while send data over websocket: {err}")
            return False