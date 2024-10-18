from datetime import datetime
from http import HTTPStatus

from abstractions.service import IService

from errors.bad_input_error import BadInputError

from models.user import User

from repositories.sql.sqlite.user import UserRepository

from start_utils import db_session

from utilities.jwt import JWTUtility


class UserAuthenticateService(IService):

    def __init__(self, urn: str = None, user_urn: str = None, api_name: str = None) -> None:
        super().__init__(urn, user_urn, api_name)
        self.urn = urn
        self.user_urn = user_urn
        self.api_name = api_name

        self.jwt_utility = JWTUtility(urn=self.urn)
        self.user_repository = UserRepository(
            urn=self.urn,
            user_urn=self.user_urn,
            api_name=self.api_name,
            session=db_session
        )

    async def run(self, data: dict) -> dict:

        self.logger.debug("Fetching token")
        token: str = data.get("token")
        self.logger.debug("Fetched token")

        if not token:
            raise BadInputError(
                response_message="token cannot be null or empty.",
                response_key="error_authorisation_failed",
                http_status_code=HTTPStatus.BAD_REQUEST
            )
        
        try:

            token_payload: dict = self.jwt_utility.decode_token(
                token=token
            )
        
        except Exception as err:

            self.logger.error(f"Error occured while decoding token: {err}")
            raise BadInputError(
                response_message="Invalid token",
                response_key="error_authorisation_failed",
                http_status_code=HTTPStatus.BAD_REQUEST
            )
    
        self.logger.debug("Fething user")
        user: User = self.user_repository.retrieve_record_by_email_and_is_logged_in(
            email=token_payload.get("email"),
            is_logged_in=True,
            is_deleted=False
        )
        self.logger.debug("Fethed user")

        if not user:
            raise BadInputError(
                response_message="User not Found. Incorrect email or password.",
                response_key="error_authorisation_failed",
                http_status_code=HTTPStatus.BAD_REQUEST
            )
        
        self.logger.debug("Updating logged in status")
        user: User = self.user_repository.update_record(
            id=user.id,
            new_data={
                "is_logged_in": True,
                "last_login": datetime.now()
            }
        )
        self.logger.debug("Updated logged in status")

        return {
            "status": user.is_logged_in,
            "token": token,
            "session_urn": user.urn
        }

        