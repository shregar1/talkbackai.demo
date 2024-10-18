import os

from hashlib import md5
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing_extensions import Any, List
from ulid import ulid

from services.apis.rag.abstraction import IRAGService

from start_utils import embeddings_function

from utilities.websockets import WebsocketUtility


class BuildRetrievalAugmentedGenerationService(IRAGService):

    def __init__(self, urn: str, **kwargs: Any) -> 'BuildRetrievalAugmentedGenerationService':
        self.urn = urn
        super().__init__(urn, **kwargs)
        self.websocket_utility = WebsocketUtility(urn=self.urn)
        self.logger.debug("Initializing Retrieval Augmented Generation (RAG) service")

    async def __fetch_document_loader(self, file_type: str, document_path: str) -> PyPDFLoader:
        
        self.logger.debug("Fetching document loader")
        document_loader = PyPDFLoader(file_path=document_path)
        self.logger.debug("Fetched document loader")
        
        return document_loader

    async def __load_and_split_documents(
        self, 
        document_loader: PyPDFLoader,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[Document]:

        self.logger.debug("Loading documents")
        documents = document_loader.load()
        self.logger.debug("Loaded documents")

        self.logger.debug("Splitting documents")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap
        )
        document_splits: List[Document] = text_splitter.split_documents(documents)
        self.logger.debug("Splitted documents")

        return document_splits

    async def __update_document_metadata(self, documents: List[Document]) -> List[Document]:

        self.logger.debug("Updating document metadata")
        for document in documents:
            metadata = document.metadata
            source = metadata.get("source")
            page = metadata.get("page")
            document.metadata.update(
                {
                    "id": md5(f"{source}_{page}_{ulid()}".encode("utf-8")).hexdigest()
                }
            )
        self.logger.debug("Updated document metadata")

        return documents
    
    async def __add_documents_to_vector_store(self, vector_store: FAISS, documents: List[Document]) -> None:

        self.logger.debug("Adding new documents")
        vector_store.add_documents(documents)
        self.logger.debug("Added new documents")

        return None

    async def run(self, data: dict):

        try:

            session_id: str = data.get("session_id")
            chat_urn: str = data.get("chat_urn")
            chat_type: str = data.get("chat_type")
            file_type: str = data.get("file_type")
            document_file_path: str = data.get("document_file_path")

            self.logger.debug("Fetch Document Loader")
            document_loader = await self.__fetch_document_loader(
                file_type=file_type,
                document_path=document_file_path
            )
            self.logger.debug("Fetched Document Loader")

            self.logger.debug("Load Document")
            documents = await self.__load_and_split_documents(
                document_loader=document_loader,
            )
            self.logger.debug("Loaded Document")

            self.logger.debug("Updating document metadata")
            documents = await self.__update_document_metadata(
                documents=documents
            )
            self.logger.debug("Updated document metadata")

            vector_store_dir_path: str = os.path.join("vector_store", f"{session_id}_{chat_urn}_vector_store")

            if vector_store_dir_path and os.path.exists(vector_store_dir_path):

                self.logger.debug("Creating FAISS vector store")
                vector_store: FAISS = await self.load_vector_store(
                    vector_store_dir_path=vector_store_dir_path,
                    embeddings_function=embeddings_function
                )
                self.logger.debug("Created FAISS vector store")

                self.logger.debug("Updating Documents to FAISS Index")
                await self.__add_documents_to_vector_store(
                    vector_store=vector_store,
                    documents=documents
                )
                self.logger.debug("Updated Documents to FAISS Index")

            else:

                self.logger.debug("Loading FAISS vector store")
                vector_store: FAISS = await self.create_vector_store(
                    documents=documents,
                    embeddings_function=embeddings_function
                )
                self.logger.debug("Loaded FAISS vector store")

            self.logger.debug("Saving vector store")
            await self.save_vector_store(
                vector_store_dir_path=vector_store_dir_path,
                vector_store=vector_store
            )
            self.logger.debug("Saving vector store")

            return {
                "status": True,
                "session_id": session_id,
                "chat_urn": chat_urn,
                "chat_type": chat_type,
                "task": "build"
            }

        except Exception as err:
            self.logger.error(f"Exception occurred while building retrieval-augmented generation. err: {err}")
            raise err

        finally:

            self.logger.debug("Removing temp file")
            try:
                if os.path.exists(document_file_path):
                    os.remove(document_file_path)
            except Exception as err:
                self.logger.error(err)
                pass
            self.logger.debug("Removed temp file")

            self.logger.debug("Completed Build RAG Service")