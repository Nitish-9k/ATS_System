import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import routes
from backend.core.config import(
    ALLOWED_ORIGINS,
    APP_DESCRIPTION,
    APP_VERSION,
    APP_TITLE,
    SPACY_MODEL_PRIMARY,
    SPACY_MODEL_SECONDARY,
    SENTENCE_MODEL_TRANSFORMER
)

# from backend.api.routes import router 

logger = logging.getLogger("ats_resume_scorer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting ATS Resume analyze api")

    logger.info(f"loading spacy nlp model: {SPACY_MODEL_PRIMARY}")
    import spacy

    try:
        app.state.nlp = spacy.load(SPACY_MODEL_PRIMARY)
        logger.info(f"Loaded {SPACY_MODEL_PRIMARY}")
    except OSError:
        logger.warning(f"{SPACY_MODEL_PRIMARY} not found - falling back to {SPACY_MODEL_SECONDARY}")
        app.state.nlp = spacy.load(SPACY_MODEL_SECONDARY)
        logger.info(f"Loaded {SPACY_MODEL_SECONDARY} (fallback)")

    logger.info("All models loaded. API is ready to serve requests")

    try:
        yield
    finally:
        logger.info("shutting down the api")


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"

)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[*ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routes if present
if hasattr(routes, "router"):
    app.include_router(routes.router)
else:
    logger.warning("No router found in backend.api.routes — no endpoints registered")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        'backend.main:app',
        host='0.0.0.0',
        port=8000,
        reload=True,  # auto-restart on code changes (dev only)
    )
