from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain.schema import Document
from typing_extensions import Any, List

from abstractions.service import IService

from repositories.nosql.cassandra.messages import Messages, MessagesRepository

from utilities.websockets import WebsocketUtility


class IRAGService(IService):

    def __init__(self, urn: str, **kwargs: Any) -> 'IRAGService':

        self.urn = urn
        super().__init__(urn, **kwargs)
        
        self.websocket_utility = WebsocketUtility(urn=self.urn)
        self.messages_repository = MessagesRepository(urn=self.urn)


        self.logger.debug("Initializing Initiate Chat API service")

    async def create_vector_store(self, documents: List[Document], embeddings_function: Embeddings) -> FAISS:

        self.logger.debug("Creating vector store")
        vector_store: FAISS = FAISS.from_documents(documents=documents, embedding=embeddings_function)
        self.logger.debug("Created vector_store")

        return vector_store
    
    async def load_vector_store(self, vector_store_dir_path: str, embeddings_function: Embeddings) -> FAISS:

        self.logger.debug("Loading existing vector store")
        vector_store: FAISS = FAISS.load_local(
            vector_store_dir_path, 
            embeddings_function, 
            allow_dangerous_deserialization=True
        )
        self.logger.debug("Loaded existing vector store")

        return vector_store

    async def save_vector_store(
        self,
        vector_store: FAISS,
        vector_store_dir_path: str
    ) -> None:
        
        self.logger.debug(f"Saving vector store to dir: {vector_store_dir_path}")
        vector_store.save_local(vector_store_dir_path)
        self.logger.debug(f"Saved vector store to dir: {vector_store_dir_path}")

        return vector_store_dir_path
    
    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    async def record_message_in_database(self, message_data: dict, metadata: dict):

        self.logger.debug("Recording messgaes in database")
        message: Messages = self.messages_repository.create_record(
            urn=message_data.get("urn"),
            chat_urn=message_data.get("chat_urn"),
            text=message_data.get("text"),
            sender_urn=message_data.get("sender_urn"),
            receiver_urn=message_data.get("receiver_urn"),
            sender_name=message_data.get("sender_name"),
            receiver_name=message_data.get("receiver_name"),
            message_type=message_data.get("message_type"),
            chat_type=message_data.get("chat_type"),
            metadata=message_data.get("metadata")
        )
        message_data.update({
            "timestamp": str(message.time_stamp)
        })
        message_data.update(metadata)
        self.logger.debug("Recorded messgaes in database")

        return message_data