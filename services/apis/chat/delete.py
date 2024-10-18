from typing import Any, List, Dict

from abstractions.service import IService

from constants.api_status import APIStatus

from dtos.responses.base import BaseResponseDTO

from repositories.nosql.cassandra.messages import MessagesRepository

from start_utils import redis_session

from utilities.websockets import WebsocketUtility


class DeleteChatService(IService):

    def __init__(self, urn: str, **kwargs: Any) -> 'DeleteChatService':

        self.urn = urn
        super().__init__(urn, **kwargs)
        
        self.messages_repository = MessagesRepository(urn=self.urn)
        self.websocket_utility = WebsocketUtility(urn=self.urn)
        self.logger.debug("Initializing Ftech chats API service")
    
    async def delete_chat(self, chat_urn: str, user_urn: str) -> bool:

        try:

            self.logger.debug(f"Deleting chat with chat urn: {chat_urn}")
            status = self.messages_repository.delete_messages_by_chat_urn(
                chat_urn=chat_urn
            )
            self.logger.debug(f"Deleted chat with chat urn: {chat_urn}")

            if redis_session.exists(chat_urn):
                self.logger.debug("Chat exists in cache")

                self.logger.debug("Deleting chat from cache")
                redis_session.delete(chat_urn)
                self.logger.debug("Chat successfully deleted from cache")

            else:
                self.logger.debug("Chat does not exist in cache")

            return status
        
        except Exception as err:
            self.logger.error(f"An error occured while deleteing chat {err}")
    
            return False

    async def run(self, data: dict) -> dict:
            
        try:

            self.logger.debug("Fetching user urn")
            chat_urn: str = data.get("chat_urn")
            user_urn: str = data.get("user_urn")
            self.logger.debug("Fetching user urn")

            self.logger.debug("Fetching messages")
            messages: List[Dict[str, str]] = await self.delete_chat(
                chat_urn=chat_urn,
                user_urn=user_urn
            )

            self.logger.debug("Preparing delete Chat response DTO")
            response_payload = {
                "status": True,
                "chat_urn": chat_urn
            }
            response_dto: BaseResponseDTO = BaseResponseDTO(
                transaction_urn=self.urn,
                status=APIStatus.SUCCESS,
                response_message="Successfully deleted chats.",
                response_key="success_delete_chat",
                data=response_payload
            )
            self.logger.debug("Prepared delete Chat response DTO")

            return response_dto

        except Exception as err:

            self.logger.error(f"Exception occurred while running delete chat service: {err}")
            raise err
        
        finally:

            self.logger.debug("Completed delete Chat Service")