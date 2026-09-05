import io 
import magic 
from typing import tuple, Optional

import pdfplumber
from docx import Document
import PyPDF2

from backend.utills.file_utils import (
    FileParsingError,
    TextExtractionError,
    FileUploadError,
    log_error,
    log_warning,
    log_info,
    with_fallback
    )

from backend.core.config import (
    SUPPORTED_FILE_TYPES,
    SUPPORTED_FILE_EXTENSIONS,
    MAX_FILE_SIZE_MB,
    ALLOWED_FILE_TYPES,
    MAX_FILE_SIZE_BYTES,
    SUPPORTED_MIME_TYPES
)

class FileParsingError(Exception):
    pass

class FilevalidationError(Exception):
    pass        


def validate_file(file_data: bytes, filename: str) -> Tuple[bool,str,Optional[str]]:
    """
    Validate the uploaded file based on its type and size.

    Args:
        file_data (bytes): The content of the uploaded file.
        filename (str): The name of the uploaded file.

    Returns:
        Tuple[bool, str, Optional[str]]: A tuple containing a boolean indicating if the file is valid,
                                         a message describing the validation result, and an optional
                                         error message if the file is invalid.
    """
    # Check file size
    file_size=len(file_data)
    if file_size> MAX_FILE_SIZE_BYTES:
        size_mb = file_size/ (1024 * 1024)
        return False, f"File size ({size_mb:.2f} MB) exceeds the maximum limit of {MAX_FILE_SIZE_MB} MB.", None


    if file_size==0:
        return False ,"File is empty. Please upload a valid file.", None

    try:

    # Check file type using magic
        mime_type = magic.from_buffer(file_data, mime=True)
    except Exception as e:
        return False,f"Error determining file type: {str(e)}", None
    

    if mime_type not in SUPPORTED_MIME_TYPES:
        supported=", ".join(SUPPORTED_MIME_TYPES.keys()).upper()
        return False, f"Unsupported file type: {mime_type}. Supported types are: {supported}.", None
        
    return True, "File is valid.", mime_type

