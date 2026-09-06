import io
import mimetypes
import re
from typing import Optional, Tuple

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
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    SUPPORTED_EXTENSIONS,
    SUPPORTED_MIME_TYPES,
)

try:
    import magic
except ImportError:
    magic = None

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

    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    mime_type = None
    if magic is not None:
        try:
            mime_type = magic.from_buffer(file_data, mime=True)
        except Exception:
            mime_type = None

    if mime_type not in SUPPORTED_MIME_TYPES:
        mime_type = mimetypes.types_map.get(extension)
        signatures = {
            ".pdf": (b"%PDF", "application/pdf"),
            ".docx": (
                b"PK",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        }
        signature = signatures.get(extension)
        if signature:
            mime_type = signature[1] if file_data.startswith(signature[0]) else None
    

    if mime_type not in SUPPORTED_MIME_TYPES or extension not in SUPPORTED_EXTENSIONS:
        supported=", ".join(SUPPORTED_MIME_TYPES.keys()).upper()
        return (
            False,
            f"Unsupported file type or extension: {mime_type}. "
            f"Supported types are: {supported}.",
            None,
        )
        
    return True, "File is valid.", mime_type


def extract_text(file_data: bytes, filename: str) -> str:
    """Extract text from supported resume formats."""
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    try:
        if extension == ".pdf":
            with pdfplumber.open(io.BytesIO(file_data)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif extension == ".docx":
            document = Document(io.BytesIO(file_data))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        elif extension == ".doc":
            raise FileParsingError("Legacy .doc files are not supported for text extraction.")
        else:
            raise FileParsingError("Unsupported resume extension.")
    except FileParsingError:
        raise
    except Exception as error:
        raise TextExtractionError(f"Unable to extract text from {filename}.") from error

    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        raise TextExtractionError("The uploaded resume contains no extractable text.")
    return normalized
