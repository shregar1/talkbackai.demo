from fastapi import APIRouter

from controllers.apis.chat.delete import DeleteChatController
from controllers.apis.chat.fetch import FetchChatsController
from controllers.apis.chat.match import MatchUsersChatController
from controllers.apis.rag.build import BuildRAGController

from start_utils import logger

router = APIRouter(prefix="/apis")

logger.debug(f"Registering {BuildRAGController.__name__} route.")
router.add_api_route(
    path="/rag/build/{session_id}/{chat_urn}",
    endpoint=BuildRAGController().post,
    methods=["POST"]
)
logger.debug(f"Registered {BuildRAGController.__name__} route.")

logger.debug(f"Registering {FetchChatsController.__name__} route.")
router.add_api_route(
    path="/chat/fetch/{user_urn}",
    endpoint=FetchChatsController().post,
    methods=["POST"]
)
logger.debug(f"Registered {FetchChatsController.__name__} route.")

logger.debug(f"Registering {DeleteChatController.__name__} route.")
router.add_api_route(
    path="/chat/delete/{user_urn}",
    endpoint=DeleteChatController().delete,
    methods=["DELETE"]
)
logger.debug(f"Registered {DeleteChatController.__name__} route.")

logger.debug(f"Registering {MatchUsersChatController.__name__} route.")
router.add_api_route(
    path="/chat/match/{user_urn}",
    endpoint=MatchUsersChatController().post,
    methods=["POST"]
)
logger.debug(f"Registered {MatchUsersChatController.__name__} route.")