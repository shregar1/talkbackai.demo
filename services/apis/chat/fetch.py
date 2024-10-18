import json
import pandas as pd
import numpy as np

from langchain_core.messages import AIMessage, HumanMessage
from typing import Any, List, Dict

from abstractions.service import IService

from constants.api_status import APIStatus

from dtos.responses.base import BaseResponseDTO

from repositories.nosql.cassandra.messages import Messages, MessagesRepository

from start_utils import AI_USER_URN, redis_session

from utilities.websockets import WebsocketUtility


class FetchChatsService(IService):

    def __init__(self, urn: str, **kwargs: Any) -> 'FetchChatsService':

        self.urn = urn
        super().__init__(urn, **kwargs)
        
        self.messages_repository = MessagesRepository(urn=self.urn)
        self.websocket_utility = WebsocketUtility(urn=self.urn)
        self.logger.debug("Initializing Ftech chats API service")

    def serialize_message(self, message: Messages, user_urn: str) -> dict:
        """
        Serialize a Messages object to a dictionary that can be returned as JSON.
        """
        return {
            "urn": message.urn,
            "session_id": user_urn,
            "chat_urn": message.chat_urn,
            "timestamp": message.time_stamp.isoformat() if message.time_stamp else None,
            "text": message.text,
            "sender_urn": message.sender_urn,
            "receiver_urn": message.receiver_urn,
            "sender_name": message.sender_name,
            "receiver_name": message.receiver_name,
            "message_type": message.message_type,
            "chat_type": message.chat_type,
            **message.metadata
        }

    async def build_conversation(self, messages: List[Dict[str, str]]):

        conversation = []
        self.logger.debug("Preparing conversation.")
        for message in messages:

            if message.get("message_type") == "text":

                if message.get("sender_urn") == AI_USER_URN:
                    conversation.append({
                        "ai": message.get("text")
                    })
                else:
                    conversation.append(
                        {
                            "human": message.get("text")
                        }
                    )
        self.logger.debug("Prepared conversation.")
        return conversation
    
    async def fetch_chats(self, user_urn: str, chat_type: str = None):
        messages = self.messages_repository.fetch_user_messages(
            user_urn=user_urn,
            chat_type=chat_type
        )

        chats = {}
        if messages:

            self.logger.debug("Serialising merssages")
            serialized_messages = [self.serialize_message(message, user_urn) for message in messages]
            self.logger.debug("Serialised merssages")

            self.logger.debug("Fetching chat groups")
            df = pd.DataFrame(data=serialized_messages)
            df = df.replace({np.nan: None})
            group_by_gen = df.groupby(["chat_urn"])

            chats = {}
            for group_id, df_group in group_by_gen:
                
                self.logger.debug("Fetching chat urn")
                chat_urn: str = str(group_id[0])
                self.logger.debug("Fetched chat urn")

                self.logger.debug(f"Preparing chat with chat_urn: {chat_urn}")
                df_group_sorted = df_group.sort_values(by='timestamp', ascending=True)
                df_group_sorted.fillna(value="")
                messages: List[Dict[str, str]] = df_group_sorted.to_dict("records")
                chats[chat_urn] = {
                    "urn": messages[0].get("chat_urn", ""),
                    "messageKey": messages[0].get("chat_urn", ""),
                    "timestamp": messages[0].get("timestamp", ""),
                    "messages": messages,
                    "chatType": messages[0].get("chat_type", "")
                }
                self.logger.debug(f"Prepared chat with chat_urn: {chat_urn}")
                
                if not redis_session.exists(chat_urn):
                    self.logger.debug("Converstaion does not exist in cache")

                    self.logger.debug("Build conversation")
                    conversation = await self.build_conversation(messages=messages)
                    redis_session.set(chat_urn, json.dumps(conversation))
                    self.logger.debug("Built conversation")
                
                else:

                    self.logger.debug("Converstaion already exists in cache")
                    pass

        return chats

    async def run(self, data: dict) -> dict:
            
        try:

            self.logger.debug("Fetching user urn")
            user_urn: str = data.get("user_urn")
            chat_type: str = data.get("chat_type")
            self.logger.debug("Fetching user urn")

            self.logger.debug("Fetching messages")
            messages: List[Dict[str, str]] = await self.fetch_chats(
                user_urn=user_urn,
                chat_type=chat_type
            )

            self.logger.debug("Preparing Fetch Chats response DTO")
            response_payload = {
                "chats": messages,
                "user_urn": user_urn
            }
            response_dto: BaseResponseDTO = BaseResponseDTO(
                transaction_urn=self.urn,
                status=APIStatus.SUCCESS,
                response_message="Successfully fetched chats.",
                response_key="success_fetch_chats",
                data=response_payload
            )
            self.logger.debug("Prepared Fetch Chats response DTO")

            return response_dto

        except Exception as err:

            self.logger.error(f"Exception occurred while running ftech chats service: {err}")
            raise err
        
        finally:

            self.logger.debug("Completed fetch Chats Service")