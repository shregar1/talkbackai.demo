import os
import faiss
import numpy as np

from datetime import datetime
from fastapi import WebSocket
from langchain_core.embeddings import Embeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models.base import BaseLanguageModel
from langchain.prompts import PromptTemplate
from langchain.vectorstores.base import VectorStoreRetriever
from langchain_community.vectorstores import FAISS
from typing_extensions import Any, Callable, Dict, List
from ulid import ulid

from repositories.nosql.cassandra.messages import Messages, MessagesRepository

from repositories.sql.sqlite.user import User, UserRepository

from services.apis.rag.abstraction import IRAGService

from start_utils import AI_USER_URN, AI_USER_NAME, db_session, embeddings_function, rag_llm_model, rag_prompt, websockets_store

from utilities.websockets import WebsocketUtility


class QueryRetrivalAugmentedGenerationService(IRAGService):

    def __init__(self, urn: str, **kwargs: Any) -> 'QueryRetrivalAugmentedGenerationService':
        self.urn = urn
        super().__init__(urn, **kwargs)
        self.user_repository = UserRepository(urn=self.urn, session=db_session)
        self.messages_repository = MessagesRepository(urn=self.urn)
        self.websocket_utility = WebsocketUtility(urn=self.urn)
        self.logger.debug("Initializing Initiate Chat API service")

    async def __load_retriever(
        self, 
        vector_store: FAISS
    ) -> Any:
        """
        Load the FAISS retriever.
        """
        self.logger.debug("Loading FAISS retriever")
        retriever: VectorStoreRetriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 6})
        self.logger.debug("Loaded FAISS retriever")
        return retriever

    async def __build_rag_chain(
        self,
        retriever: VectorStoreRetriever,
        format_docs: Callable,
        rag_prompt: PromptTemplate,
        model: BaseLanguageModel
    ) -> Any:
        """
        Build the Retrieval-Augmented Generation (RAG) chain.
        """
        self.logger.debug("Building rag chain")
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | rag_prompt
            | model
            | StrOutputParser()
        )
        self.logger.debug("Built rag chain")
        return rag_chain

    async def __invoke_rag_chain(self, rag_chain: Any, query_prompt: str) -> str:
        """
        Invoke the RAG chain to get a response based on the input query.
        """
        self.logger.debug("Invoking rag chain")
        response_message: str = rag_chain.invoke(query_prompt)
        self.logger.debug("Invoked rag chain")
        return response_message

    async def run(self, data: dict):

        try:

            self.logger.debug("Fetching chat urn")
            session_id: str = data.get("session_id")
            chat_urn: str = data.get("chat_urn")
            chat_type: str = data.get("chat_type")
            prompt: str = data.get("prompt")
            self.logger.debug("Fetched chat urn")

            self.logger.debug(f"Fetching user: {session_id}")
            user: User = self.user_repository.retrieve_record_by_urn(
                urn=session_id,
                is_deleted=False
            )
            self.logger.debug(f"Fetched user: {user.id}")

            self.logger.debug("Creating messgaes in database")
            metadata: Dict[str, str] = {}
            message_data: Dict[str, str] = {
                "urn": str(ulid()),
                "chat_urn": chat_urn,
                "text": prompt,
                "sender_urn": user.urn,
                "receiver_urn": AI_USER_URN,
                "sender_name": f"{user.first_name} {user.last_name}",
                "receiver_name":  AI_USER_NAME,
                "message_type": "text",
                "chat_type": chat_type,
                "metadata": metadata
            }

            text_message_data = await self.record_message_in_database(
                message_data=message_data,
                metadata=metadata
            )

            text_message_data.update({
                "sender_name": "you"
            })
            self.logger.debug("Created messgaes in database")

            vector_store_dir_path: str = os.path.join("vector_store", f"{session_id}_{chat_urn}_vector_store")

            if os.path.exists(vector_store_dir_path):

                self.logger.debug(f"Fetch FAISS Index: {vector_store_dir_path}")
                vector_store: FAISS = await self.load_vector_store(
                    vector_store_dir_path=vector_store_dir_path,
                    embeddings_function=embeddings_function
                )
                self.logger.debug("Fetched FAISS Index")

                self.logger.debug("Fetch FAISS retriever")
                retriever: VectorStoreRetriever = await self.__load_retriever(vector_store=vector_store)
                self.logger.debug("Fetched FAISS retriever")

                self.logger.debug("Build rag chain")
                rag_chain = await self.__build_rag_chain(
                    retriever=retriever,
                    format_docs=self.format_docs,
                    rag_prompt=rag_prompt,
                    model=rag_llm_model
                )
                self.logger.debug("Built rag chain")

                self.logger.debug("Invoking rag")
                response_message: str = await self.__invoke_rag_chain(
                    rag_chain=rag_chain,
                    query_prompt=prompt
                )
                self.logger.debug("Invoked rag")

            else:

                response_message: str = "Please upload a pdf file to build a rag."

            self.logger.debug(f"Fetching user: {session_id}")
            user: User = self.user_repository.retrieve_record_by_urn(
                urn=session_id,
                is_deleted=False
            )
            self.logger.debug(f"Fetched user: {user.id}")

            self.logger.debug("Creating messgaes in database")
            metadata: Dict[str, str] = {}
            message_data: Dict[str, str] = {
                "urn": str(ulid()),
                "chat_urn": chat_urn,
                "text": response_message,
                "sender_urn": AI_USER_URN,
                "receiver_urn": user.urn,
                "sender_name": AI_USER_NAME,
                "receiver_name": f"{user.first_name} {user.last_name}",
                "message_type": "text",
                "chat_type": chat_type,
                "metadata": metadata
            }

            text_message_data = await self.record_message_in_database(
                message_data=message_data,
                metadata=metadata
            )

            text_message_data.update({
                "sender_name": "you"
            })
            self.logger.debug("Created messgaes in database")

            self.logger.debug(f"Fetching websocket connection for the session: {session_id}")
            websocket_connection: WebSocket = websockets_store.get(session_id)

            try:

                self.logger.debug("Sending json data over websocket")
                event_data: List[Dict[str, str]] = [
                    {
                        "text": response_message,
                        "sender_name": "ai",
                        "message_type": "text",
                        "timestamp": f"{str(datetime.now().time().hour)}:{str(datetime.now().time().minute)}"
                    }
                ]
                await self.websocket_utility.send_json(
                    websocket=websocket_connection,
                    event_data=event_data
                )
                self.logger.debug("Sent json data over websocket")
            
            except Exception as err:
                self.logger.error(f"Failed to send json data over websocket. err: {err}")

            return {
                "response_message": response_message,
                "session_id": session_id,
                "chat_urn": chat_urn
            }

        except Exception as err:
            self.logger.error(f"Exception occurred while querying retrieval-augmented generation. err: {err}")
            raise err

        finally:

            self.logger.debug("Completed Query RAG Service")