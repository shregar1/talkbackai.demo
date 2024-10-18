from ulid import ulid

from abstractions.event import IEvent

from services.apis.model.text_to_image import TextToImageChatService
from services.apis.model.text_to_code import TextToCodeChatService
from services.apis.model.text_to_speech import TextToSpeechChatService


from start_utils import on_event


class WebSocketMessageTextEvent(IEvent):

    @on_event(r'^message/text/image_generation$')
    async def image_generation(cls, data: dict):

        try:

            cls.logger.debug("Running Text to Image service")
            text_to_image_chat_service = TextToImageChatService(
                urn=ulid()
            )

            _ = await text_to_image_chat_service.run(
                data={
                    "chat_type": data.get("chat_type"),
                    "session_id": data.get("session_id"),
                    "chat_urn": data.get("chat_urn"),
                    "prompt": data.get("text")
                }
            )
            cls.logger.debug("Completed Text to Image service")
        
        except Exception:
            cls.logger("Failed to run text to speech service")

    @on_event(r'^message/text/text_generation$')
    async def text_generation(cls, data: dict):
    
        try:

            cls.logger.debug("Running Text to Speech service")
            text_chat_service = TextToSpeechChatService(
                urn=ulid()
            )

            _ = await text_chat_service.run(
                data={
                    "chat_type": data.get("chat_type"),
                    "session_id": data.get("session_id"),
                    "chat_urn": data.get("chat_urn"),
                    "message": data.get("text")
                }
            )
            cls.logger.debug("Running Text to Speech service")

        except Exception:
            cls.logger("Failed to run text to speech service")

    @on_event(r'^message/text/code_generation$')
    async def text_generation(cls, data: dict):

        try:

            cls.logger.debug("Running Text to Code service")
            text_chat_service = TextToCodeChatService(
                urn=ulid()
            )

            _ = await text_chat_service.run(
                data={
                    "chat_type": data.get("chat_type"),
                    "session_id": data.get("session_id"),
                    "chat_urn": data.get("chat_urn"),
                    "prompt": data.get("text")
                }
            )
            cls.logger.debug("Running Text to Code service")

        except Exception:
            cls.logger("Failed to run text to Code service")