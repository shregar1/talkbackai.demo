import base64
import io
import os
import re
import time

from datetime import datetime
from fastapi import WebSocket
from langchain_core.messages import AIMessage, HumanMessage
from gtts import gTTS
from PIL import Image
from openai import RateLimitError
from google.api_core.exceptions import ResourceExhausted
from typing import Any, List, Dict, Union

from abstractions.service import IService

from repositories.nosql.cassandra.messages import Messages, MessagesRepository

from start_utils import conversation_llm, speech_recognition, speech_recognizer, gradio_flux_client

from utilities.websockets import WebsocketUtility


class IModelService(IService):

    def __init__(self, urn: str, **kwargs: Any) -> 'IModelService':

        self.urn = urn
        super().__init__(urn, **kwargs)
        
        self.messages_repository = MessagesRepository(urn=self.urn)
        self.websocket_utility = WebsocketUtility(urn=self.urn)
        self.logger.debug("Initializing Initiate Chat API service")


    async def build_chat(self, conversation: List[Dict[str, str]]):

        chat = []
        self.logger.debug("Preparing chat.")
        for message in conversation:
            if "ai" in message:
                chat.append(AIMessage(content=message.get("ai", "")))
            else:
                chat.append(HumanMessage(content=message.get("human", "")))
        self.logger.debug("Prepared chat.")

        return chat
    
    async def invoke_conversation_model(self, chat: List[Union[AIMessage, HumanMessage]]) -> str:

        self.logger.debug("Invoking chat llm")
        try:
            
            ai_message: AIMessage = conversation_llm.invoke(chat)
            self.logger.debug("Invoked chat llm")
            
            self.logger.debug("Extracting message content")
            message: str = ai_message.content if getattr(ai_message, "content", None) else ai_message
            self.logger.debug("Extracted message content")

            return message
        
        except (RateLimitError, ResourceExhausted):
            self.logger.error("RateLimitError occured while invoking llm")
            return "You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors."
        
        except Exception as err:
            self.logger.error(f"Error occured while invoking llm: {type(err), err}")
            
            return "Unexpected Error occured while invoking llm."

    async def transcribe_audio_message(self, input_file_path: str) -> str:
        
        try:

            self.logger.debug("Converting speech to text")
            self.logger.debug("Loading WAV file.")
            with speech_recognition.AudioFile(input_file_path) as source:  # pass the file path, not the file object
                
                self.logger.debug("Reading the entire audio file.")
                audio_data = speech_recognizer.record(source)
                self.logger.debug("Read the entire audio file.")

            try:

                self.logger.debug("Transcribing text")
                text = speech_recognizer.recognize_google(audio_data)
                self.logger.debug("Transcribed text:", text)

                return text

            except speech_recognition.UnknownValueError as err:
                self.logger.debug(f"Google Speech Recognition could not understand the audio. {err}")
                raise RuntimeError("Google Speech Recognition could not understand the audio.")

            except speech_recognition.RequestError as err:
                self.logger.debug(f"Could not request results from Google Speech Recognition service; {err}")
                raise RuntimeError("Google Speech Recognition could not understand the audio.")
            
        except Exception as err:

            self.logger.error(f"Failed to transacribe audio message. {err}")
            raise RuntimeError("Failed to transacribe audio message")

        finally:

            self.logger.debug("Removing temp file")
            try:
                if os.path.exists(input_file_path):
                    os.remove(input_file_path)
            except Exception as err:
                self.logger.error(err)
                pass
            self.logger.debug("Removed temp file")

    async def clean_llm_output(self, llm_output: str):
        # Step 1: Remove bullet points (*, -) and hashtags (#)
        cleaned_text = re.sub(r'[*#-]\s*', '', llm_output)
        
        # Step 2: Remove multiple newlines and extra spaces
        cleaned_text = re.sub(r'\n+', ' ', cleaned_text)  # Replace newlines with space
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()  # Remove extra spaces
        
        return cleaned_text

    async def audioinscribe_message(self, message: str, audio_file_path: str, websocket_connection: WebSocket = None, stream: bool = False) -> str:
        
        self.logger.debug("Audio-Inscribing message")
        language = 'en'  # English language
        tts = gTTS(text=message, lang=language, slow=False)
        self.logger.debug("Audio-Inscribed message")

        self.logger.debug("Sending json data over websocket")
        event_data: List[Dict[str, str]] = [
            {
                "text": message,
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

        if stream and websocket_connection:

            self.logger.debug("Streaming audio file")
            chunk_generator = tts.stream()
            try:
                count = 0
                while True:
                    chunk_bytes = next(chunk_generator)
                    await self.websocket_utility.send_bytes(
                        websocket=websocket_connection,
                        event_data=chunk_bytes
                    )
                    with open(f"temp/{count}.mp3", "wb") as f:
                        f.write(chunk_bytes)
                    count += 1
                    time.sleep(0.1)
            except StopIteration:
                self.logger.debug("Generator is exhausted")
                pass
            self.logger.debug("Streamed audio file")
            
        else:

            self.logger.debug("Saving audio file to temp store")
            tts.save(audio_file_path)
            self.logger.debug("Saved audio file to temp store")

        return audio_file_path

    async def extract_code_blocks(self, llm_output: str):
        """
        Extracts code blocks enclosed in triple backticks along with the language.

        Args:
        llm_output (str): The string containing potential code blocks.

        Returns:
        List[Dict]: A list of dictionaries, each containing 'language' and 'code'.
        """
        # Regex pattern to match code blocks with optional language specifier
        pattern = r'```(\w+)?\n([\s\S]*?)```'
        
        # Find all matches
        matches = re.findall(pattern, llm_output)
        
        # Format result as a list of dictionaries with language and code
        code_blocks = []
        for match in matches:
            language = match[0] if match[0] else "unknown"
            code = match[1].strip()
            code_blocks.append({
                "language": language,
                "code": code
            })
        
        return code_blocks

    async def generate_image(self, prompt: str):
        
        self.logger.debug(f"Generating image for prompt: {prompt}")

        try:

            result = gradio_flux_client.predict(
                    prompt=prompt,
                    seed=0,
                    randomize_seed=True,
                    width=1024,
                    height=1024,
                    num_inference_steps=4,
                    api_name="/infer"
            )

            file_path: str = result[0]
            image: Image = Image.open(file_path)
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            img_base64 = f"data:image/png;base64,{img_base64}"
            os.remove(file_path)

            return {
                "img_base64": img_base64,
                "message": "Here is your generated image.",
            }

        except Exception as err:
            self.logger.error(f"Exception occured while generating image: {err}")
            return {
                "img_base64": None,
                "message": "Sorry couldn't generate the image. Please try again later.",
            }
        
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

    async def run(self, data: dict) -> dict:
        pass