import json
import random

from typing import Any, List, Dict
from ulid import ulid

from abstractions.service import IService

from constants.api_status import APIStatus

from dtos.responses.base import BaseResponseDTO

from repositories.nosql.cassandra.messages import MessagesRepository

from start_utils import redis_session, websockets_store

from utilities.websockets import WebsocketUtility


class MatchUsersChatService(IService):

    def __init__(self, urn: str, **kwargs: Any) -> 'MatchUsersChatService':

        self.urn = urn
        super().__init__(urn, **kwargs)
        
        self.messages_repository = MessagesRepository(urn=self.urn)
        self.websocket_utility = WebsocketUtility(urn=self.urn)
        self.logger.debug("Initializing Ftech chats API service")
    
    async def match(self, user_urn: str) -> bool:

        self.logger.debug("Fetching available wesocket connections")
        available_keys = [key for key in websockets_store.keys() if key != user_urn]
        self.logger.debug("Fetched available wesocket connections")

        self.logger.debug("Matching with random connection")
        if available_keys:

            self.logger.debug("Matched with random connection")
            reciever_urn = random.choice(available_keys)
            return reciever_urn

        else:
            return None 

    async def run(self, data: dict) -> dict:
            
        try:

            self.logger.debug("Fetching user urn")
            chat_urn: str = data.get("chat_urn")
            sender_urn: str = data.get("user_urn")
            self.logger.debug("Fetching user urn")

            self.logger.debug("Loading conversation from session")
            chat_urn: str = ulid()
            conversations = redis_session.get(chat_urn)
            if conversations is None:
                conversations = {}
            else:
                conversations: Dict[str, str] = json.loads(conversations)
            self.logger.debug("Loaded conversation from session")

            self.logger.debug("Match users")
            reciever_urn: str = await self.match(
                user_urn=sender_urn
            )
            self.logger.debug("Matched users")

            self.logger.debug("Update converstaion store")
            conversations.update(
                {
                    chat_urn: {
                        "sender": sender_urn,
                        "reciever": reciever_urn
                    }
                }
            )
            redis_session.setex(chat_urn, 24*60*60, json.dumps(conversations))
            self.logger.debug("Updated converstaion store")

            self.logger.debug("Preparing match users response DTO")
            response_payload = {
                "status": True,
                "chat_urn": chat_urn,
                "chat_users": {
                    "sender": sender_urn,
                    "reciever": reciever_urn
                }
            }

            response_dto: BaseResponseDTO = BaseResponseDTO(
                transaction_urn=self.urn,
                status=APIStatus.SUCCESS,
                response_message="Successfully matched users.",
                response_key="success_matched_users",
                data=response_payload
            )
            self.logger.debug("Prepared match users response DTO")

            return response_dto

        except Exception as err:

            self.logger.error(f"Exception occurred while running match users service: {err}")
            raise err
        
        finally:

            self.logger.debug("Completed match users Service")