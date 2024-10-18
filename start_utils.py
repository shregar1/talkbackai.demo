import os
import re
import redis
import speech_recognition
import sys

from cassandra.cqlengine import connection
from cassandra.auth import PlainTextAuthProvider
from celery import Celery
from fastapi import WebSocket
from gradio_client import Client
#from langchain_openai import ChatOpenAI
from langchain import hub
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.base import BaseLanguageModel
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from typing_extensions import Dict, Callable
from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from transformers import BlipProcessor, BlipForConditionalGeneration

from configurations.cache import CacheConfiguration, CacheConfigurationDTO
from configurations.celery import CeleryConfiguration, CeleryConfigurationDTO
from configurations.db import DBConfiguration, DBConfigurationDTO

logger.debug("Initialising websocket connection store")
websockets_store: Dict[str, WebSocket] = {}
logger.debug("Initialising websocket connection store")

logger.debug("Initialising websocket event registry")
event_registry: Dict[re.Pattern, Callable] = {}
logger.debug("Initialising websocket event registry")

logger.debug("Initialising peer connection store")
peer_connection_store: Dict[str, WebSocket] = {}
logger.debug("Initialising peer connection store")

logger.debug("Initialising websocket router")
websocket_router: Dict[str, object] = {}
logger.debug("Initialising websocket router")

logger.add(sys.stderr, colorize=True, format="<green>{time:MMMM-D-YYYY}</green> | <black>{time:HH:mm:ss}</black> | <level>{level}</level> | <cyan>{message}</cyan> | <magenta>{name}:{function}:{line}</magenta> | <yellow>{extra}</yellow>")

logger.debug("Setting up on_event websocket decorator.")
def on_event(event_pattern):
    """
    A decorator that registers a function to a regex event pattern.
    """
    def decorator(func):
        logger.debug(f"Registering event: {event_pattern}")
        event_registry[re.compile(event_pattern)] = func
        logger.debug(event_registry)
        return func
    return decorator
logger.debug("Set up on_event websocket decorator.")

logger.debug("Initialising trigger websocker event method.")
async def trigger_event(event_name, *args, **kwargs):
    """
    Function to trigger an event by matching the event_name against registered regex patterns.
    """
    logger.debug(f"Triggering event: {event_name}")
    for pattern, func in event_registry.items():
        match = pattern.match(event_name)

        if match:

            logger.debug(f"Event matched: {event_name}")
            class_name: str = func.__qualname__.split(".")[0]
            cls = websocket_router.get(class_name)

            if cls is None:
                raise RuntimeError(f"Found no websocket handler class with name {class_name} binded to event {event_name}.")
            return await func(cls, *args, **kwargs, **match.groupdict())

    logger.debug(f"No route registered for event '{event_name}'")
    return None
logger.debug("Initialising trigger websocker event method.")

logger.debug("Loading environment variables from .env file")
load_dotenv()
logger.debug("Loaded environment variables from .env file")

logger.info("Loading environment variables")
APP_NAME: str = os.environ.get('APP_NAME')
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
HUGGING_FACE_API_KEY: str = os.getenv("HUGGING_FACE_API_KEY")
LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY")
SECRET_KEY: str = os.getenv("SECRET_KEY")
BCRYPT_SALT: str = os.getenv("BCRYPT_SALT")
HS256_ALGORITHM: str = os.getenv("HS256_ALGORITHM")
RS256_ALGORITHM: str = os.getenv("RS256_ALGORITHM")
GOOGLE_JWKS_URL: str = os.getenv("GOOGLE_JWKS_URL")
GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
TEMP_FOLDER: str = os.getenv("TEMP_FOLDER")
CASSANDRA_HOST: str = os.getenv("CASSANDRA_HOST")
CASSANDRA_USER: str = os.getenv("CASSANDRA_USER")
CASSANDRA_PASSWORD: str = os.getenv("CASSANDRA_PASSWORD")
CASSANDRA_DEFAULT_KEYSPACE: str = os.getenv("CASSANDRA_DEFAULT_KEYSPACE")
AI_USER_URN: str = os.getenv("AI_USER_URN")
AI_USER_NAME: str = os.getenv("AI_USER_NAME")
MESSAGE_TTL: int = int(os.getenv("MESSAGE_TTL"))
logger.info("Loaded environment variables")

if not os.path.exists(TEMP_FOLDER):
    os.mkdir(TEMP_FOLDER)

ROOT_PATH = os.getcwd()

logger.info("Loading Configurations")
cache_configuration: CacheConfigurationDTO = CacheConfiguration().get_config()
celery_configuration: CeleryConfigurationDTO = CeleryConfiguration().get_config()
db_configuration: DBConfigurationDTO = DBConfiguration().get_config()
logger.info("Loaded Configurations")

logger.info("Initializing SQL database")
engine = create_engine('sqlite:///talkback_ai.db')
Session = sessionmaker(bind=engine)
db_session = Session()
Base = declarative_base()
logger.info("Initialized SQL database")

logger.info("Initializing NoSQL database")
def casssandra_connection():
    auth_provider = PlainTextAuthProvider(username=CASSANDRA_USER, password=CASSANDRA_PASSWORD)
    connection.setup(
        hosts=[CASSANDRA_HOST], 
        default_keyspace=CASSANDRA_DEFAULT_KEYSPACE, 
        protocol_version=3, 
        auth_provider=auth_provider
    )
    return None
logger.info("Initialized NoSQL database")

logger.info("Initializing Redis database")
redis_session = redis.Redis(
    host=cache_configuration.host,
    port=cache_configuration.port,
    password=cache_configuration.password
)

if not redis_session:
    raise RuntimeError("No Redis session available")
logger.info("Initialized Redis database")


logger.info("Initializing Celery")
redis_url: str = celery_configuration.backend_url.format(
    password=cache_configuration.password,
    host=cache_configuration.host,
    port=cache_configuration.port,
    db=celery_configuration.db
)
celery = Celery(
    APP_NAME,
    backend=redis_url,
    broker=redis_url,
    include=[
        "tasks.delete",
    ]
)
logger.info("Initialized Celery")

logger.info("Initializing speech recognizer")
speech_recognizer = speech_recognition.Recognizer()
logger.info("Initialized speech recognizer")

logger.info("Initializing conversation llm")
#conversation_llm: BaseLanguageModel = ChatOpenAI(model="gpt-4o")
#conversation_llm = OllamaLLM(model="llama3.1")
conversation_llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=GOOGLE_API_KEY)
rag_llm_model: BaseLanguageModel = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=GOOGLE_API_KEY)
logger.info("Initialised conversation llm")

logger.info("Initialising Embedding function")
embeddings_function: Embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
logger.debug("Initialised Embedding function")

logger.debug("Initialising rag prompt")
rag_prompt = hub.pull("rlm/rag-prompt")
logger.debug("Initialised rag prompt")

logger.info("Initialising image captioning model")
image_captioning_processor =  BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
image_captioning_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
logger.info("Initialised image captioning model")

logger.debug("Initialising gradio flux client")
gradio_flux_client = Client("black-forest-labs/FLUX.1-schnell", download_files=TEMP_FOLDER)
logger.debug("Initialised gradio flux client")

logger.debug("Initialising gradio code client")
gradio_code_client = Client("Tonic/Yi-Coder-9B")
logger.debug("Initialised gradio code clinet")

logger.debug("Initialising unprotected routes")
unprotected_routes: set = {
    "/user/register",
    "/user/login"
}
logger.debug("Initialised unprotected routes")