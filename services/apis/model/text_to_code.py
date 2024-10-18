import json
import os

from datetime import datetime
from fastapi import WebSocket
from langchain_core.messages import AIMessage, HumanMessage
from typing import Any, List, Dict, Union
from ulid import ulid

from repositories.nosql.cassandra.messages import Messages, MessagesRepository

from repositories.sql.sqlite.user import User, UserRepository

from services.apis.model.abstraction import IModelService

from start_utils import AI_USER_URN, AI_USER_NAME, db_session, redis_session, websockets_store

from utilities.websockets import WebsocketUtility


class TextToCodeChatService(IModelService):

    def __init__(self, urn: str, **kwargs: Any) -> 'TextToCodeChatService':

        self.urn = urn
        super().__init__(urn, **kwargs)
        self.messages_repository = MessagesRepository(urn=self.urn)
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
            prompt=data.get("prompt")
            self.logger.debug(f"Fetched chat urn {prompt}")

            self.logger.debug("Loading conversation from session")
            conversation = redis_session.get(chat_urn)
            if conversation is None:
                conversation = []
            else:
                conversation: List[Dict[str, str]] = json.loads(conversation)
            self.logger.debug("Loaded conversation from session")

            self.logger.debug(f"Fetching websocket connection for the session: {session_id}")
            websocket_connection: WebSocket = websockets_store.get(session_id)

            self.logger.debug("Appending transcribed message to conversation")
            conversation.append(
                {
                    "human": prompt
                }
            )
            self.logger.debug("Appended transcribed message to conversation")

            self.logger.debug("Building chat context from conversation")
            chat: List[Union[AIMessage, HumanMessage]] = await self.build_chat(conversation=conversation)
            self.logger.debug("Built chat context from conversation")

            chat.append(HumanMessage(content="You are a helpful coding assistant. Provide clear and concise code examples."))

            self.logger.debug("Invoking conversation llm")
            response_message: str = await self.invoke_conversation_model(chat=chat)
            self.logger.debug("Invoked conversation llm")

            self.logger.debug("Cleaning llm response")
            response_code_blocks: List[Dict[str, str]] = await self.extract_code_blocks(llm_output=response_message)
            self.logger.debug("Cleaned llm response")

            self.logger.debug(response_code_blocks)

            self.logger.debug(f"Fetching user: {session_id}")
            user: User = self.user_repository.retrieve_record_by_urn(
                urn=session_id,
                is_deleted=False
            )
            self.logger.debug(f"Fetched user: {user.id}")

            for response_code_block in response_code_blocks:

                self.logger.debug("Appending ai response message to conversation")
                conversation.append(
                    {
                        "ai": response_code_block.get("code")
                    }
                )
                self.logger.debug("Appended ai response message to conversation")

                self.logger.debug(f"Storing chat in session with urn: {chat_urn}")
                redis_session.set(chat_urn, json.dumps(conversation))
                self.logger.debug(f"Stored chat in session with urn: {chat_urn}")

                self.logger.debug("Recording messgaes in database")
                metadata: Dict[str, str] = {
                    "language": response_code_block.get("language")
                }
                message_data: Dict[str, str] = {
                    "urn": str(ulid()),
                    "chat_urn": chat_urn,
                    "text": response_code_block.get("code"),
                    "sender_urn": AI_USER_URN,
                    "receiver_urn": user.urn,
                    "sender_name": AI_USER_NAME,
                    "receiver_name": f"{user.first_name} {user.last_name}",
                    "message_type": "code",
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
                message_data.update(metadata)
                self.logger.debug("Recorded messgaes in database")

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
                "message": response_message,
                "time": str(date_time.time()),
                "chat_urn": chat_urn
            }
            self.logger.debug("Prepared Conversate Chat response DTO")

            return response_payload

        except Exception as err:

            self.logger.error(f"Exception occurred while running intitate chat service: {err}")
            raise err
        
        finally:

            self.logger.debug("Completed Conversate Chat Service")
            
            