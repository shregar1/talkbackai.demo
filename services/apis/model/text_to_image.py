from datetime import datetime
from fastapi import WebSocket
from typing import Any, List, Dict
from ulid import ulid

from repositories.nosql.cassandra.messages import Messages, MessagesRepository

from repositories.sql.sqlite.user import User, UserRepository

from services.apis.model.abstraction import IModelService

from start_utils import AI_USER_URN, AI_USER_NAME, db_session, websockets_store

from utilities.websockets import WebsocketUtility


class TextToImageChatService(IModelService):
    def __init__(self, urn: str, **kwargs: Any) -> "TextToImageChatService":
        self.urn = urn
        super().__init__(urn, **kwargs)
        self.messages_repository = MessagesRepository(urn=self.urn)
        self.user_repository = UserRepository(urn=self.urn, session=db_session)

        self.websocket_utility = WebsocketUtility(urn=self.urn)

        self.logger.debug("Initializing Initiate Chat API service")

    async def run(self, data: dict) -> dict:
        self.logger.debug("Starting Text to Image Chat Service")

        try:

            self.logger.debug("Fetching chat urn")
            session_id: str = data.get("session_id")
            chat_urn: str = data.get("chat_urn")
            chat_type: str = data.get("chat_type")
            prompt: str = data.get("prompt")
            self.logger.debug("Fetched chat urn")

            self.logger.debug("Generating image for given prompt")
            response_data: dict = await self.generate_image(prompt=prompt)
            self.logger.debug("Generated image for given prompt")

            self.logger.debug(f"Fetching user: {session_id}")
            user: User = self.user_repository.retrieve_record_by_urn(
                urn=session_id,
                is_deleted=False
            )
            self.logger.debug(f"Fetched user: {user.id}")

            self.logger.debug("Creating messgaes in database")
            metadata: Dict[str, str] = {}
            message_data: Dict[str, str] = {
                "urn": str(ulid()),
                "chat_urn": chat_urn,
                "text": response_data.get("message"),
                "sender_urn": AI_USER_URN,
                "receiver_urn": user.urn,
                "sender_name": AI_USER_NAME,
                "receiver_name": f"{user.first_name} {user.last_name}",
                "message_type": "text",
                "chat_type": chat_type,
                "metadata": metadata
            }

            text_message_data = await self.record_message_in_database(
                message_data=message_data,
                metadata=metadata
            )
            self.logger.debug("Created messgaes in database")

            if response_data.get("img_base64", None):

                self.logger.debug("Creating messgaes in database")
                metadata: Dict[str, str] = {}
                message_data: Dict[str, str] = {
                    "urn": str(ulid()),
                    "chat_urn": chat_urn,
                    "text": response_data.get("img_base64"),
                    "sender_urn": AI_USER_URN,
                    "receiver_urn": user.urn,
                    "sender_name": AI_USER_NAME,
                    "receiver_name": f"{user.first_name} {user.last_name}",
                    "message_type": "image",
                    "chat_type": chat_type,
                    "metadata": metadata
                }

                image_message_data = await self.record_message_in_database(
                    message_data=message_data,
                    metadata=metadata
                )
                self.logger.debug("Created messgaes in database")

            self.logger.debug(f"Fetching websocket connection for the session: {session_id}")
            websocket_connection: WebSocket = websockets_store.get(session_id)

            if websocket_connection:

                try:

                    self.logger.debug("Sending json data over websocket")
                    event_data: List[Dict[str, str]] = [text_message_data]

                    if response_data.get("img_base64", None):
                        event_data.append(image_message_data)
                    
                    await self.websocket_utility.send_json(
                        websocket=websocket_connection,
                        event_data=event_data)
                    self.logger.debug("Sent json data over websocket")

                except Exception as err:

                    self.logger.error(f"An error occured while sending data over websocket: {err}")
                    pass

            self.logger.debug("Preparing Conversate Chat response DTO")
            date_time = datetime.now()
            response_payload = {
                "image_base64": response_data.get("img_base64"),
                "message": response_data.get("message"),
                "time": str(date_time.time()),
                "chat_urn": chat_urn,
            }
            self.logger.debug("Prepared Conversate Chat response DTO")

            return response_payload

        except Exception as err:
            self.logger.error(f"Exception occurred while running intitate chat service: {err}")
            raise err

        finally:
            self.logger.debug("Completed Text to Image Chat Service")
