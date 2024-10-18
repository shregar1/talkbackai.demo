import json
import os

from datetime import datetime
from fastapi import WebSocket
from typing import Any, List, Dict
from ulid import ulid

from repositories.sql.sqlite.user import User, UserRepository

from services.apis.model.abstraction import IModelService

from start_utils import AI_USER_URN, AI_USER_NAME, db_session, redis_session, websockets_store

from utilities.websockets import WebsocketUtility


class SpeechToTextChatService(IModelService):

    def __init__(self, urn: str, **kwargs: Any) -> 'SpeechToTextChatService':

        self.urn = urn
        super().__init__(urn, **kwargs)
        self.user_repository = UserRepository(urn=self.urn, session=db_session)

        self.websocket_utility = WebsocketUtility(urn=self.urn)

        self.logger.debug("Initializing Initiate Chat API service")

    async def run(self, data: dict) -> dict:
        
        self.logger.debug("Starting Conversate Chat Service")

        try:

            self.logger.debug("Fetching chat urn")
            session_id: str = data.get("session_id")
            chat_urn: str = data.get("chat_urn")
            chat_type: str = data.get("chat_type")
            input_file_path=data.get("audio_file_path")
            self.logger.debug("Fetched chat urn")

            self.logger.debug("Loading conversation from session")
            conversation = redis_session.get(chat_urn)
            if conversation is None:
                conversation = []
            else:
                conversation: List[Dict[str, str]] = json.loads(conversation)
            self.logger.debug("Loaded conversation from session")

            self.logger.debug("Trasncribing audio message")
            transcribed_message: str = await self.transcribe_audio_message(
                input_file_path=input_file_path
            )
            self.logger.debug("Transcribed audio message")

            self.logger.debug(f"Fetching user: {session_id}")
            user: User = self.user_repository.retrieve_record_by_urn(
                urn=session_id,
                is_deleted=False
            )
            self.logger.debug(f"Fetched user: {user.id}")

            metadata: Dict[str, str] = {}
            message_data: Dict[str, str] = {
                "urn": str(ulid()),
                "chat_urn": chat_urn,
                "text": transcribed_message,
                "sender_urn": user.urn,
                "receiver_urn": AI_USER_URN,
                "sender_name": f"{user.first_name} {user.last_name}",
                "receiver_name": AI_USER_NAME,
                "message_type": "text",
                "chat_type": chat_type,
                "metadata": metadata
            }

            self.logger.debug(f"Fetching websocket connection for the session: {session_id}")
            websocket_connection: WebSocket = websockets_store.get(session_id)

            if websocket_connection:

                try:

                    self.logger.debug("Sending json data over websocket")
                    event_data: List[Dict[str, str]] =[message_data]
                    await self.websocket_utility.send_json(
                        websocket=websocket_connection,
                        event_data=event_data
                    )
                    self.logger.debug("Sending json data over websocket")
                
                except Exception as err:

                    self.logger.error(f"An error occured while sending data over websocket: {err}")
                    pass

            self.logger.debug("Preparing Conversate Chat response DTO")
            date_time = datetime.now()
            response_payload = {
                "message": transcribed_message,
                "time": str(date_time.time()),
                "chat_urn": chat_urn,
                **message_data
            }
            self.logger.debug("Prepared Conversate Chat response DTO")

            return response_payload

        except Exception as err:

            self.logger.error(f"Exception occurred while running intitate chat service: {err}")
            raise err
        
        finally:

            self.logger.debug("Removing temp file")
            try:
                if os.path.exists(input_file_path):
                    os.remove(input_file_path)
            except Exception as err:
                self.logger.error(err)
                pass
            self.logger.debug("Removed temp file")

            self.logger.debug("Completed Conversate Chat Service")
            
            