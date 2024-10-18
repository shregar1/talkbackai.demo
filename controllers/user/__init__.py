from fastapi import APIRouter
from controllers.user.login import LoginController
from controllers.user.logout import LogoutController
from controllers.user.register import RegisterController
from controllers.user.authenticate import AuthenticateController
from start_utils import logger

router = APIRouter(prefix="/user")

logger.debug(f"Registering {RegisterController.__name__} route.")
router.add_api_route(
    path="/register",
    endpoint=RegisterController().post,
    methods=["POST"]
)
logger.debug(f"Registered {RegisterController.__name__} route.")

logger.debug(f"Registering {LoginController.__name__} route.")
router.add_api_route(
    path="/login",
    endpoint=LoginController().post,
    methods=["POST"]
)
logger.debug(f"Registered {LoginController.__name__} route.")

logger.debug(f"Registering {AuthenticateController.__name__} route.")
router.add_api_route(
    path="/authenticate",
    endpoint=AuthenticateController().post,
    methods=["POST"]
)
logger.debug(f"Registered {AuthenticateController.__name__} route.")

logger.debug(f"Registering {LogoutController.__name__} route.")
router.add_api_route(
    path="/logout",
    endpoint=LogoutController().post,
    methods=["POST"]
)
logger.debug(f"Registered {LogoutController.__name__} route.")

