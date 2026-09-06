import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import routes
from backend.core.config import (
    ALLOWED_ORIGINS,
    APP_DESCRIPTION,
    APP_VERSION,
    APP_TITLE,
    SPACY_MODEL_PRIMARY,
    SPACY_MODEL_SECONDARY,
)

# from backend.api.routes import router 

logger = logging.getLogger("ats_resume_scorer")
<<<<<<< HEAD
=======

>>>>>>> b018ef731707e198b24bbd85677f38b6c0bc9357

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting ATS Resume analyze api")

    logger.info(f"loading spacy nlp model: {SPACY_MODEL_PRIMARY}")
    import spacy

    try:
        app.state.nlp = spacy.load(SPACY_MODEL_PRIMARY)
<<<<<<< HEAD
        logger.info("Loaded %s", SPACY_MODEL_PRIMARY)
    except OSError:
        logger.warning(
            "%s not found - falling back to %s",
            SPACY_MODEL_PRIMARY,
            SPACY_MODEL_SECONDARY,
        )
        try:
            app.state.nlp = spacy.load(SPACY_MODEL_SECONDARY)
            logger.info("Loaded %s (fallback)", SPACY_MODEL_SECONDARY)
        except OSError:
            logger.warning("No configured spaCy model found; using a blank English model")
            app.state.nlp = spacy.blank("en")

    logger.info("All models loaded. API is ready to serve requests")
    from backend.database.local_db import init_db
    init_db()
=======
        logger.info(f"Loaded {SPACY_MODEL_PRIMARY}")
    except OSError:
        logger.warning(f"{SPACY_MODEL_PRIMARY} not found - falling back to {SPACY_MODEL_SECONDARY}")
        app.state.nlp = spacy.load(SPACY_MODEL_SECONDARY)
        logger.info(f"Loaded {SPACY_MODEL_SECONDARY} (fallback)")

    logger.info("All models loaded. API is ready to serve requests")
>>>>>>> b018ef731707e198b24bbd85677f38b6c0bc9357

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
<<<<<<< HEAD
    allow_origins=ALLOWED_ORIGINS,
=======
    allow_origins=[*ALLOWED_ORIGINS],
>>>>>>> b018ef731707e198b24bbd85677f38b6c0bc9357
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
app.include_router(routes.router)

if __name__ == "__main__":
    import uvicorn
=======
# include routes if present
if hasattr(routes, "router"):
    app.include_router(routes.router)
else:
    logger.warning("No router found in backend.api.routes — no endpoints registered")


if __name__ == "__main__":
    import uvicorn

>>>>>>> b018ef731707e198b24bbd85677f38b6c0bc9357
    uvicorn.run(
        'backend.main:app',
        host='0.0.0.0',
        port=8000,
        reload=True,  # auto-restart on code changes (dev only)
    )
