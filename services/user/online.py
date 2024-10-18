from typing import Dict, List

from abstractions.service import IService

from models.user import User

from repositories.sql.sqlite.user import UserRepository

from start_utils import db_session


class OnlineUsersService(IService):

    def __init__(self, urn: str = None, user_urn: str = None, api_name: str = None) -> None:
        super().__init__(urn, user_urn, api_name)
        self.urn = urn
        self.user_urn = user_urn
        self.api_name = api_name

    async def run(self, data: dict) -> List[Dict[str, str]]:

        self.logger.debug("Fetching online users")
        users: List[User] = UserRepository(
            urn=self.urn,
            user_urn=self.user_urn,
            api_name=self.api_name,
            db_session=db_session
        ).get_record_by_is_logged_in(
            is_logged_in=True,
            is_deleted=False
        )
        self.logger.debug("Fetched online users")

        self.logger.debug("Preparing online user data")
        online_user_data: list = list()
        for user in users:

            user_data: dict = {
                "id": user.id,
                "is_logged_in": user.is_logged_in
            }

            online_user_data.append(user_data)
        self.logger.debug("Prepared online user data")

        return user_data

        