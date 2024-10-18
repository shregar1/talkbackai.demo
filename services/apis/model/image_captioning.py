import base64
import os

from datetime import datetime
from fastapi import WebSocket
from PIL import Image
from typing import Any, List, Dict
from ulid import ulid

from repositories.nosql.cassandra.messages import Messages, MessagesRepository

from repositories.sql.sqlite.user import User, UserRepository

from services.apis.model.abstraction import IModelService

from start_utils import AI_USER_URN, AI_USER_NAME, image_captioning_model, image_captioning_processor, TEMP_FOLDER, websockets_store, db_session

from utilities.websockets import WebsocketUtility


class ImageCaptioningChatService(IModelService):

    def __init__(self, urn: str, **kwargs: Any) -> 'ImageCaptioningChatService':

        self.urn = urn
        super().__init__(urn, **kwargs)

        self.messages_repository = MessagesRepository(urn=self.urn)
        self.user_repository = UserRepository(urn=self.urn, session=db_session)

        self.websocket_utility = WebsocketUtility(urn=self.urn)

        self.logger.debug("Initializing Initiate Chat API service")

    async def __caption_image(self, input_file_path: str):
        
        raw_image = Image.open(input_file_path).convert('RGB')
        inputs = image_captioning_processor(raw_image, return_tensors="pt")

        out = image_captioning_model.generate(**inputs)
        image_caption = image_captioning_processor.decode(out[0], skip_special_tokens=True)

        return image_caption
    
    def __save_base64_as_image(self, base64_string: str, output_file_path: str):
        base64_string = base64_string.split(",")[1]
        img_data = base64.b64decode(base64_string)

        with open(output_file_path, 'wb') as f:
            f.write(img_data)
        
        return None
    
    async def run(self, data: dict) -> dict:
        
        self.logger.debug("Starting Conversate Chat Service")

        try:

            self.logger.debug("Fetching chat urn")
            session_id: str = data.get("session_id")
            chat_urn: str = data.get("chat_urn")
            chat_type: str = data.get("chat_type")
            image_bas64: str = data.get("image")
            self.logger.debug("Fetched chat urn")

            image_file_path = os.path.join(TEMP_FOLDER, f"{self.urn}_CHAT_{chat_urn}_{str(datetime.now().timestamp())}.png")
            self.logger.debug(f"Saving image to temp store: {image_file_path}")
            self.__save_base64_as_image(base64_string=image_bas64, output_file_path=image_file_path)
            self.logger.debug(f"Saved image to temp _store: {image_file_path}")

            self.logger.debug(f"Fetching user: {session_id}")
            user: User = self.user_repository.retrieve_record_by_urn(
                urn=session_id,
                is_deleted=False
            )
            self.logger.debug(f"Fetched user: {user.id}")

            self.logger.debug("Recording messgaes in database")
            metadata: Dict[str, str] = {}
            message_data: Dict[str, str] = {
                "urn": str(ulid()),
                "chat_urn": chat_urn,
                "text": image_bas64,
                "sender_urn": user.urn,
                "receiver_urn": AI_USER_URN,
                "sender_name": f"{user.first_name} {user.last_name}",
                "receiver_name": AI_USER_NAME,
                "message_type": "image",
                "chat_type": chat_type,
                "metadata": metadata
            }
            message_data: Dict[str, str] = await self.record_message_in_database(
                message_data=message_data,
                metadata=metadata
            )
            message_data.update({
                "sender_name": "you"
            })
            self.logger.debug("Recorded messgaes in database")

            self.logger.debug("Captioning image message")
            image_caption: str = await self.__caption_image(
                input_file_path=image_file_path
            )
            self.logger.debug("Captioned imaged message")

            self.logger.debug("Recording messgaes in database")
            metadata: Dict[str, str] = {}
            message_data: Dict[str, str] = {
                "urn": str(ulid()),
                "chat_urn": chat_urn,
                "text": image_caption,
                "sender_urn": AI_USER_URN,
                "receiver_urn": user.urn,
                "sender_name": AI_USER_NAME,
                "receiver_name": f"{user.first_name} {user.last_name}",
                "message_type": "text",
                "chat_type": chat_type,
                "metadata": metadata
            }
            message_data: Dict[str, str] = await self.record_message_in_database(
                message_data=message_data,
                metadata=metadata
            )
            self.logger.debug("Recorded messgaes in database")

            audio_file_path = os.path.join(TEMP_FOLDER, f"{self.urn}_CHAT_{chat_urn}_{str(datetime.now().timestamp())}.wav")
            self.logger.debug("Audio Inscribing message")
            await self.audioinscribe_message(message=image_caption, audio_file_path=audio_file_path)
            self.logger.debug("Audio Inscribed message")

            self.logger.debug(f"Fetching websocket connection for the session: {session_id}")
            websocket_connection: WebSocket = websockets_store.get(session_id)
            self.logger

            if websocket_connection:

                try:

                    self.logger.debug("Sending json data over websocket")
                    event_data: List[Dict[str, str]] = [message_data]
                    await self.websocket_utility.send_json(
                        websocket=websocket_connection,
                        event_data=event_data 
                    )
                    self.logger.debug("Sent json data over websocket")

                    if not data.get("is_transaciption_required"):

                        self.logger.debug("Sending Audio bytes over websocket")
                        with open(audio_file_path, "rb") as f:
                            data = f.read()
                            await self.websocket_utility.send_bytes(
                                websocket=websocket_connection, 
                                event_data=data
                            )
                        self.logger.debug("Sent Audio bytes over websocket")
                
                except Exception as err:

                    self.logger.error(f"An error occured while sending data over websocket: {err}")
                    pass

            self.logger.debug("Preparing Conversate Chat response DTO")
            date_time = datetime.now()
            response_payload = {
                "audio_file_path": audio_file_path,
                "time_stamp": str(date_time.time()),
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
                if os.path.exists(image_file_path):
                    os.remove(image_file_path)
            except Exception as err:
                self.logger.error(err)
                pass
            self.logger.debug("Removed temp file")

            self.logger.debug("Completed Conversate Chat Service")
            
            