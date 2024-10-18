import os

from pydub import AudioSegment

from abstractions.utility import IUtility

from start_utils import TEMP_FOLDER

from utilities.base64 import Base64Utility


class AudioUtility(IUtility):

    def __init__(self, urn: str = None) -> None:
        super().__init__(urn)
        self.urn = urn
        self.base64_utility = Base64Utility(urn=self.urn)

    async def convert_bytes_to_wav(self, audio_bytes: bytes, filename: str) -> str:
        
        self.logger.debug("Saving audio files to temp store")
        file_path = os.path.join(TEMP_FOLDER, filename)
        with open(file_path, "wb") as buffer:
            buffer.write(audio_bytes)
        self.logger.debug("Saved audio files to temp store")

        self.logger.debug("Saving audio file as high bit rate wav.")
        audio = AudioSegment.from_file(file_path)
        high_bitrate_file = os.path.join(TEMP_FOLDER, f"{self.urn}_{filename}.wav")
        audio.export(high_bitrate_file, format="wav", bitrate="320k")
        self.logger.debug("Saving audio file as high bit rate wav.")

        self.logger.debug("Removing temporary file")
        os.remove(file_path)
        self.logger.debug("Removed temporary file")

        return high_bitrate_file
    
    async def convert_base64_to_wav(self, audio_base64: str, filename: str) -> str:
        
        self.logger.debug("Converting Audio base64 to bytes")
        audio_bytes: bytes = await self.base64_utility.base64_to_bytes(
            base64_string=audio_base64
        )
        self.logger.debug("Converted Audio base64 to bytes")

        self.logger.debug("Converting Audio bytes to WAV")
        audio_file_path: str = await self.convert_bytes_to_wav(
            audio_bytes=audio_bytes,
            filename=filename
        )
        self.logger.debug("Converted Audio bytes to WAV")

        return audio_file_path
