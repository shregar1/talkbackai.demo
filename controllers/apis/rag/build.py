import os

from datetime import datetime
from fastapi import Request, Path
from fastapi.responses import JSONResponse
from http import HTTPStatus
from pydantic import ValidationError
from typing_extensions import Annotated

from abstractions.controller import IController

from constants.api_lk import APILK
from constants.api_status import APIStatus
from constants.payload_type import PayloadType

from dtos.requests.apis.rag.build import BuildRAGRequestDTO
from dtos.responses.base import BaseResponseDTO

from errors.bad_input_error import BadInputError

from services.apis.rag.build import BuildRetrievalAugmentedGenerationService

from start_utils import TEMP_FOLDER


class BuildRAGController(IController):

    def __init__(self, urn: str = None) -> None:
        super().__init__(urn)
        self.api_name = APILK.CHAT_CONVERSATE
        self.payload_type = PayloadType.FORM

    async def post(self, request: Request, session_id: Annotated[str, Path(title="The sessin id")], chat_urn: Annotated[str, Path(title="The chat urn")])-> dict:
       
        self.logger.debug("Starting Build RAG Controller Execution.")
        start_time = datetime.now()

        try:

            self.urn = request.state.urn

            self.logger.debug("Validating Request", urn=self.urn)
            await self.validate_request(request=request)
            self.logger.debug("Validated Request", urn=self.urn)

            self.logger.debug("Validating Request Payload", urn=self.urn)
            request_dto: BuildRAGRequestDTO = await self.valid_post_request()
            self.logger.debug("Validating Request Payload", urn=self.urn)

            self.logger.debug("Preparing request payload for service")
            request_payload = request_dto.model_dump()
            request_payload.update(
                {
                    "chat_urn": chat_urn,
                    "session_id": session_id,
                    "chat_type": "rag"
                }
            )
            self.logger.debug("Prepared request payload for service")

            self.logger.debug("Running Build RAG Service")
            build_rag_service: BuildRetrievalAugmentedGenerationService = BuildRetrievalAugmentedGenerationService(
                urn=self.urn
            )
            build_rag_response_data: dict = await build_rag_service.run(
                data=request_payload
            )
            self.logger.debug("Completed Build RAG Service")

            http_status_code = HTTPStatus.OK
            self.logger.debug("Preparing response payload.")
            self.logger.debug("Prepared response payload.")

            return build_rag_response_data

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
            self.logger.debug("Completed Build RAG Controller Execution.")
            self.logger.debug(f"Execution took {str(end_time-start_time)}")
    
    async def valid_post_request(self):

        try:

            file = self.request_payload.get("document")
            file_path = os.path.join(TEMP_FOLDER, file.filename)
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            return BuildRAGRequestDTO(
                reference_number=self.request_payload.get("reference_number"),
                document_file_path=file_path
            )

        except ValidationError as err:

            error = err.errors()[0]
            raise BadInputError(
                response_message=error.get("msg"),
                response_key=f"error_invalid_{error.get('loc')[0]}",
                http_status_code=HTTPStatus.BAD_REQUEST
            )
