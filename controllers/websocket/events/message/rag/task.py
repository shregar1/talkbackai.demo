from ulid import ulid

from abstractions.event import IEvent

from services.apis.rag.query import QueryRetrivalAugmentedGenerationService

from start_utils import on_event


class WebSocketMessageRAGEvent(IEvent):

    @on_event(r'^message/text/rag/query$')
    async def text_generation(cls, data: dict):
    
        try:

            cls.logger.debug("Running query rag service")
            query_rag_chat_service = QueryRetrivalAugmentedGenerationService(
                urn=ulid()
            )

            _ = await query_rag_chat_service.run(
                data={
                    "chat_type": data.get("chat_type"),
                    "session_id": data.get("session_id"),
                    "chat_urn": data.get("chat_urn"),
                    "prompt": data.get("text")
                }
            )
            cls.logger.debug("Running query rag service")

        except Exception:
            cls.logger("Failed to run query rag service")