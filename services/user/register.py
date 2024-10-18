import bcrypt
import os
import ulid

from datetime import datetime
from http import HTTPStatus

from abstractions.service import IService

from errors.bad_input_error import BadInputError

from models.user import User

from repositories.sql.sqlite.user import UserRepository

from start_utils import db_session, BCRYPT_SALT


class UserRegistrationService(IService):

    def __init__(self, urn: str = None, user_urn: str = None, api_name: str = None) -> None:
        super().__init__(urn, user_urn, api_name)
        self.urn = urn
        self.user_urn = user_urn
        self.api_name = api_name

        self.user_repository = UserRepository(
            urn=self.urn,
            user_urn=self.user_urn,
            api_name=self.api_name,
            session=db_session
        )

    async def run(self, data: dict) -> dict:

        try:

            self.logger.debug("Checking if user exists")
            user: User = self.user_repository.retrieve_record_by_email(
                email=data.get("email")
            )

            if user:

                self.logger.debug("User already exists")
                raise BadInputError(
                    response_message="Email already registered. Please choose a different email address.",
                    response_key="error_email_already_registered",
                    http_status_code=HTTPStatus.BAD_REQUEST
                )

            self.logger.debug("Preparing user data")
            user: User = User(
                urn=ulid.ulid(),
                email=data.get("email"),
                password=bcrypt.hashpw(data.get("password").encode("utf-8"), BCRYPT_SALT.encode("utf8")).decode("utf8"),
                is_deleted=False,
                created_at=datetime.now()
            )
            
            user: User = self.user_repository.create_record(
                user=user
            )
            self.logger.debug("Preparing user data")

            status:str = True
            user_email: str = user.email
            created_at: str = str(user.created_at)

        except BadInputError as err:

            self.logger.error("User registration failed as user already exists")
            status:str = False
            user_email: str = getattr(user, "email", None)
            created_at: str = str(getattr(user, "created_at", None))
        
        except Exception as err:

            self.logger.error("User registration failed")
            status:str = False
            user_email: str = None
            created_at: str = None

        return {
            "status": status,
            "user_email": user_email,
            "created_at": created_at
        }

        