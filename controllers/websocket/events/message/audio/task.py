from ulid import ulid

from abstractions.event import IEvent

from services.apis.chat.speech_to_text import SpeechToTextChatService

from start_utils import on_event


class WebSocketMessageTextEvent(IEvent):

    @on_event(r'^message/audio/infer$')
    async def image_generation(cls, data: dict):
            
        try:

            cls.logger.debug("Running Speech to Text Service")
            speech_to_text_chat_service = SpeechToTextChatService(
                urn=ulid()
            )
            speech_to_text_response_data: dict = await speech_to_text_chat_service.run(
                data={
                    "chat_type": data.get("chat_type"),
                    "session_id": data.get("session_id"),
                    "chat_urn": data.get("chat_urn"),
                    "audio_file_path": data.get("audio_file_path")
                }
            )
            cls.logger.debug("Completed Speech to Text Service")

            return speech_to_text_response_data
        
        except Exception:
            cls.logger("Failed to run Speech to Text service")
