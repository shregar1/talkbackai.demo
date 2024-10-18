import base64
import os

from abstractions.utility import IUtility

from start_utils import TEMP_FOLDER

from utilities.base64 import Base64Utility


class PDFUtility(IUtility):
    
    def __init__(self, urn: str = None) -> None:
        super().__init__(urn)
        self.urn = urn
        self.base64_utility = Base64Utility(urn=self.urn)

    async def convert_base64_to_pdf(self, base64_string: str, file_path: str) -> str:
        """
        Convert a base64 string to a PDF file and save it.

        Args:
            base64_string (str): The base64 encoded string of the PDF file.
            file_path (str): The path of the file to be saved.

        Returns:
            str: The full path to the saved PDF file.
        """
        try:

            self.logger.debug("Decoding base64 string")
            pdf_bytes = self.base64_utility.decode_base64(base64_string)
            self.logger.debug("Decoded base64 string")

            self.logger.debug("Writing the PDF bytes to the file")
            with open(file_path, 'wb') as pdf_file:
                pdf_file.write(pdf_bytes)
            self.logger.debug("Written the PDF bytes to the file")

            return file_path

        except Exception as err:

            self.logger.error(f"Error converting base64 to PDF: {err}")
            raise
