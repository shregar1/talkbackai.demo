import asyncio
import json
import os
import uvicorn

from aiortc import RTCPeerConnection, RTCSessionDescription
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from ulid import ulid
from pydantic import BaseModel

from controllers.apis import router as APIRouter
from controllers.user import router as UserRouter
from controllers.websocket.events.message import router as WebSocketMessageEventRouter

from middlewares.request_context import RequestContextMiddleware

from models.user import User

from services.apis.model.speech_to_text import SpeechToTextChatService

from start_utils import Base, engine, redis_session, peer_connection_store, websockets_store, trigger_event, websocket_router

from utilities.audio import AudioUtility

logger.debug("Updating websocket router")
websocket_router.update(WebSocketMessageEventRouter)
logger.debug("Updating websocket router")

logger.debug("Creating model schema")
Base.metadata.create_all(engine)
logger.debug("Creating model schema")

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.debug("Starting up the app...")

    yield

    logger.debug("Shutting down the app...")
    coros = [peer_connection.close() for key, peer_connection in peer_connection_store.items()]
    await asyncio.gather(*coros)
    peer_connection_store.clear()

app = FastAPI(lifespan=lifespan)

load_dotenv()
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))
SSL_CERTFILE=os.getenv("SSL_CERTFILE")
SSL_KEYFILE=os.getenv("SSL_KEYFILE")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    response_payload: dict = {
        "transaction_urn": request.state.urn,
        "response_message": "Bad or missing input.",
        "response_key": "error_bad_input",
        "errors": exc.errors()
    }
    return JSONResponse(
        status_code=400,
        content=response_payload,
    )

origins = [
    "http://localhost:5173",
    "*"
]

app.add_middleware(
    middleware_class=TrustedHostMiddleware, 
    allowed_hosts=["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins for now (use specific origins in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Allows all headers
)

logger.debug("Initialising middleware stack")
app.add_middleware(RequestContextMiddleware)
logger.debug("Initialised middleware stack")

logger.debug("Initialising routers")
app.include_router(UserRouter)
app.include_router(APIRouter)
logger.debug("Initialised routers")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):

    await websocket.accept()
    logger.debug(f"Accepted connect request from user with session id: {session_id}")

    websockets_store[session_id] = websocket
    logger.debug(websockets_store)

    try:

        while True:

            data = await websocket.receive_text()
            logger.debug(f"Message received from {session_id}")
            data = json.loads(data)
            data.update({
                "session_id": session_id
            })
            logger.debug(data)
            logger.debug(data.keys())
            if data.get("event") == "message":

                if data.get("chat_type") == "rag":

                    try:

                        event_name: str = f'message/{data.get("type")}/{data.get("chat_type")}/{data.get("task")}'
                        logger.debug(f"Triggering websocket event for event:{event_name}")
                        await trigger_event(
                            event_name=event_name,
                            data=data
                        )
                        logger.debug(f"Triggering websocket event for event:{event_name}")
                    
                    except Exception:
                        logger.error(f"Failed websocket event")
                
                elif data.get("type") == "text":

                    try:

                        event_name: str = f'message/{data.get("type")}/{data.get("task")}'
                        logger.debug(f"Triggering websocket event for event:{event_name}")
                        await trigger_event(
                            event_name=event_name,
                            data=data
                        )
                        logger.debug(f"Triggering websocket event for event:{event_name}")
                    
                    except Exception:
                        logger.error(f"Failed websocket event")
                        
                if data.get("type") == "image":

                    try:

                        event_name: str = f'message/{data.get("type")}/{"captioning"}'
                        logger.debug(f"Triggering websocket event for event:{event_name}")
                        await trigger_event(
                            event_name=event_name,
                            data=data
                        )
                        logger.debug(f"Triggering websocket event for event:{event_name}")
                    
                    except Exception:
                        logger.error(f"Failed websocket event")

                if data.get("type") == "audio":
                        
                    try:

                        file_name: str = data.get("file_name")
                        audio_base64: str = data.get("audio_base64")
                        audio_base64: str = audio_base64.split(",")[1]

                        logger.debug("Converting audio base64 to wav")
                        audio_file_path: str = await AudioUtility(
                            urn=ulid()
                        ).convert_base64_to_wav(
                            audio_base64=audio_base64,
                            filename=file_name
                        )
                        logger.debug("Converted audio base64 to wav")

                        logger.debug("Running Speech to Text Chat Service")
                        speech_to_text_chat_service = SpeechToTextChatService(
                            urn=ulid()
                        )
                        data.update(
                            {
                                "session_id": session_id,
                                "audio_file_path": audio_file_path
                            }
                        )
                        speech_to_text_response_data: dict = await speech_to_text_chat_service.run(
                            data=data
                        )
                        logger.debug("Completed Speech to Text Chat Service")

                        prompt: str = speech_to_text_response_data.get("message")

                        if "image" in prompt.lower() or "images" in prompt.lower():
                            task = "image_generation"
                        else:
                            task = "text_generation"

                        data.update(
                            {
                                "task": task,
                                "text": prompt
                            }
                        )

                        event_name: str = f'message/{"text"}/{data.get("task")}'
                        logger.debug(f"Triggering websocket event for event: {event_name}")
                        await trigger_event(
                            event_name=event_name,
                            data=data
                        )
                        logger.debug(f"Triggering websocket event for event: {event_name}")

                    except Exception:
                        logger.error(f"Failed websocket event")
            
            elif data.get("event") == "acknowledgement":

                logger.debug(f"Recieved acknowledegment from {session_id}: {data.get('text')}")
            
            elif data.get("event") == "clear":

                try:

                    logger.debug("Clear session chat")
                    redis_session.set(f"{session_id}_{data.get('chat_urn')}_{data.get('chat_type')}", json.dumps([]))
                    logger.debug("Cleared session chat")
                
                except Exception:
                    logger.error(f"Failed websocket event")
            
            else:
                pass

    except WebSocketDisconnect:

        logger.debug(f"WebSocket disconnected for user {session_id}")
        websockets_store.pop(session_id, None)

class Offer(BaseModel):
    sdp: str
    type: str

@app.post("/offer")
async def offer(request: Offer):
    # Create a new PeerConnection instance
    pc = RTCPeerConnection()
    peer_connection_store.add(pc)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        print(f"ICE connection state: {pc.iceConnectionState}")
        if pc.iceConnectionState == "failed":
            await pc.close()
            peer_connection_store.discard(pc)

    # Handle the SDP offer
    offer = RTCSessionDescription(sdp=request.sdp, type=request.type)
    await pc.setRemoteDescription(offer)
    
    # Create and send SDP answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type,
    }

if __name__ == '__main__':
    logger.debug(SSL_CERTFILE)
    logger.debug(SSL_KEYFILE)
    uvicorn.run("app:app", port=PORT, host=HOST, reload=True, ssl_certfile=SSL_CERTFILE, ssl_keyfile=SSL_KEYFILE)