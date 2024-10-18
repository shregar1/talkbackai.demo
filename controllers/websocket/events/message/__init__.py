from controllers.websocket.events.message.image.task import WebSocketMessageImageEvent
from controllers.websocket.events.message.text.task import WebSocketMessageTextEvent
from controllers.websocket.events.message.rag.task import WebSocketMessageRAGEvent

from start_utils import logger

router = {}

logger.debug(f"Registering websocket route for {WebSocketMessageImageEvent.__name__}.")
router.update(
    {
        WebSocketMessageImageEvent.__name__: WebSocketMessageImageEvent
    }
)
logger.debug(f"Registering websocket route for {WebSocketMessageImageEvent.__name__}.")

logger.debug(f"Registering websocket route for {WebSocketMessageTextEvent.__name__}.")
router.update(
    {
        WebSocketMessageTextEvent.__name__: WebSocketMessageTextEvent
    }
)
logger.debug(f"Registering websocket route for {WebSocketMessageTextEvent.__name__}.")

logger.debug(f"Registering websocket route for {WebSocketMessageRAGEvent.__name__}.")
router.update(
    {
        WebSocketMessageRAGEvent.__name__: WebSocketMessageRAGEvent
    }
)
logger.debug(f"Registering websocket route for {WebSocketMessageRAGEvent.__name__}.")
