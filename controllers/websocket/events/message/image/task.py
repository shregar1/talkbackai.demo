from ulid import ulid

from abstractions.event import IEvent

from services.apis.model.image_captioning import ImageCaptioningChatService

from start_utils import on_event


class WebSocketMessageImageEvent(IEvent):

    @on_event(r'^message/image/captioning$')
    async def captioning(cls, data: dict):
            
        try:

            cls.logger.debug("Running image captioning service")
            image_captioning_chat_service = ImageCaptioningChatService(
                urn=ulid()
            )
            _ = await image_captioning_chat_service.run(
                data={
                    "chat_type": data.get("chat_type"),
                    "session_id": data.get("session_id"),
                    "chat_urn": data.get("chat_urn"),
                    "image": data.get("text")
                }
            )
            cls.logger.debug("Completed image captioning service")

        except Exception:
            cls.logger("Failed to run image captioning service")