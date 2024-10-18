import os
#
from datetime import datetime
from fastapi import Request, Path
from fastapi.responses import JSONResponse, FileResponse
from http import HTTPStatus
from pydantic import ValidationError
from pydub import AudioSegment
from typing_extensions import Annotated
#
from abstractions.controller import IController
#
from constants.api_lk import APILK
from constants.api_status import APIStatus
from constants.payload_type import PayloadType
#
from dtos.requests.apis.chat.conversate import ConversateChatRequestDTO
from dtos.responses.base import BaseResponseDTO
#
from errors.bad_input_error import BadInputError
#
from services.apis.chat.speech_to_text import SpeechToTextChatService
from services.apis.chat.text_to_speech import TextToSpeechChatService
#
from start_utils import TEMP_FOLDER, ROOT_PATH
#
from tasks.delete import delete_residual_file


class ConversateChatController(IController):

    def __init__(self, urn: str = None) -> None:
        super().__init__(urn)
        self.api_name = APILK.CHAT_CONVERSATE
        self.payload_type = PayloadType.FORM

    async def post(self, request: Request, chat_urn: Annotated[str, Path(title="The chat urn")])-> dict:
       
        self.logger.debug("Starting Conversate Chat Controller Execution.")
        start_time = datetime.now()

        try:

            self.urn = request.state.urn

            self.logger.debug("Validating Request", urn=self.urn)
            await self.validate_request(request=request)
            self.logger.debug("Validated Request", urn=self.urn)

            self.logger.debug("Validating Request Payload", urn=self.urn)
            request_dto: ConversateChatRequestDTO = await self.valid_post_request()
            self.logger.debug("Validating Request Payload", urn=self.urn)

            self.logger.debug("Preparing request payload for service")
            request_payload = request_dto.model_dump()
            request_payload.update(
                {
                    "chat_urn": chat_urn,
                }
            )
            self.logger.debug("Prepared request payload for service")

            self.logger.debug("Running Speech to Text Chat Service")
            speech_to_text_service: SpeechToTextChatService = SpeechToTextChatService(
                urn=self.urn
            )
            speech_to_text_response_data: dict = await speech_to_text_service.run(
                data=request_payload
            )
            self.logger.debug("Completed Speech to Text Chat Service")

            self.logger.debug("Running Text to Speech Chat Service")
            conversate_chat_service: TextToSpeechChatService = TextToSpeechChatService(
                urn=self.urn
            )
            response_payload = await conversate_chat_service.run(
                data={
                    "message": speech_to_text_response_data.get("message"),
                    "chat_urn": chat_urn,
                }
            )
            self.logger.debug("Completed Text to Speech Chat Service")

            http_status_code = HTTPStatus.OK
            self.logger.debug("Preparing response payload.")
            audio_file_path: str = response_payload.pop("audio_file_path", None)
            file_name: str = audio_file_path.split("/")[-1]
            response = FileResponse(path=audio_file_path, media_type="audio/mpeg", filename=file_name, headers=response_payload)
            self.logger.debug("Prepared response payload.")

            delete_residual_file.delay(file_path=os.path.join(ROOT_PATH, audio_file_path))

            return response

        except BadInputError as err:

            self.logger.error(f"{err.__class__} error occured while conversating: {err}", urn=self.urn)
            self.logger.debug("Preparing response metadata")
            response_dto: BaseResponseDTO = BaseResponseDTO(
                transaction_urn=self.urn,
                status=APIStatus.FAILED,
                response_message=err.response_message,
                response_key=err.response_key,
            )
            http_status_code = err.http_status_code
            self.logger.debug("Prepared response metadata", urn=self.urn)

            return JSONResponse(
                content=response_dto.__dict__,
                status_code=http_status_code
            )

        except Exception as err:

            self.logger.error(f"{err.__class__} error occured while conversating: {err}", urn=self.urn)

            self.logger.debug("Preparing response metadata", urn=self.urn)
            response_dto: BaseResponseDTO = BaseResponseDTO(
                transaction_urn=self.urn,
                status=APIStatus.FAILED,
                response_message="Failed to conversate.",
                response_key="error_internal_server_error",
            )
            http_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            self.logger.debug("Prepared response metadata", urn=self.urn)
    
            return JSONResponse(
                content=response_dto.__dict__,
                status_code=http_status_code
            )
        
        finally:

            end_time: datetime = datetime.now()
            self.logger.debug("Completed Conversate Chat Controller Execution.")
            self.logger.debug(f"Execution took {str(end_time-start_time)}")
    
    async def valid_post_request(self):

        try:

            file = self.request_payload.get("message_audio")
            file_path = os.path.join(TEMP_FOLDER, file.filename)
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            audio = AudioSegment.from_file(file_path)
            high_bitrate_file = os.path.join(TEMP_FOLDER, f"{self.urn}.wav")
            audio.export(high_bitrate_file, format="wav", bitrate="320k")
            os.remove(file_path)

            return ConversateChatRequestDTO(
                reference_number=self.request_payload.get("reference_number"),
                audio_file_path=high_bitrate_file
            )

        except ValidationError as err:

            error = err.errors()[0]
            raise BadInputError(
                response_message=error.get("msg"),
                response_key=f"error_invalid_{error.get('loc')[0]}",
                http_status_code=HTTPStatus.BAD_REQUEST
            )
