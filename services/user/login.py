import bcrypt
import os

from datetime import datetime
from http import HTTPStatus

from abstractions.service import IService

from errors.bad_input_error import BadInputError

from models.user import User

from repositories.sql.sqlite.user import UserRepository

from start_utils import db_session

from utilities.jwt import JWTUtility


class UserLoginService(IService):

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

        self.logger.debug("Fetching user")
        user: User = self.user_repository.retrieve_record_by_email_and_password(
            email=data.get("email"),
            password=bcrypt.hashpw(data.get("password").encode("utf8"), os.getenv("BCRYPT_SALT").encode("utf8")).decode("utf8"),
            is_deleted=False
        )
        self.logger.debug("Fetched user")

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

        payload = {
            "email": user.email,
            "created_at": str(user.created_at)
        }
        token: str = self.jwt_utility.create_access_token(
            data=payload
        )

        return {
            "status": user.is_logged_in,
            "token": token,
            "session_urn": user.urn
        }

        