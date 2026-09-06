import os
from pathlib import Path 

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# api metadata
APP_TITLE = "ATS Resume Analyzer API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Analyse resumes against job descriptions using NLP and ML."


ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
# file

MAX_FILE_SIZE_MB=5
MAX_FILE_SIZE_BYTES=MAX_FILE_SIZE_MB*1024*1024

# supported mime types and their short names
SUPPORTED_MIME_TYPES={
    "application/pdf":"pdf",
    "application/msword":"doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document":'docx',
}

SUPPORTED_EXTENSIONS = {".pdf", ".doc", ".docx"}

SPACY_MODEL_PRIMARY="en_core_web_md" #better accuracy
SPACY_MODEL_SECONDARY="en_core_web_sm"
SENTENCE_TRANSFORMER_MODEL = os.getenv(
    "SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2"
)


# score components weights -this is business logic treated as config

SCORE_WEIGHTS={
    "formatting":20,"Keywords":25,"content":25,
    "skill_validation":15,"ats_compatibility":15,
}

JD_KEYWORD_WEIGHT=0.6
JD_SEMANTIC_WEIGHT=0.4


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SUPPORTED_FILE_TYPES = set(SUPPORTED_MIME_TYPES)
ALLOWED_FILE_TYPES = SUPPORTED_MIME_TYPES
