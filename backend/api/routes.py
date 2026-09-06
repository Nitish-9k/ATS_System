import re
import json

from fastapi import APIRouter, File, Form, Header, UploadFile
from fastapi.responses import JSONResponse, Response

router = APIRouter()


def _current_user(authorization: str | None) -> dict | None:
    from backend.database.local_db import user_from_token

    token = authorization.removeprefix("Bearer ").strip() if authorization else None
    return user_from_token(token)


@router.post("/auth/signup", response_model=None)
async def signup(email: str = Form(...), password: str = Form(...)):
    from backend.database.local_db import create_user

    if len(password) < 8:
        return JSONResponse(status_code=400, content={"detail": "Password must contain at least 8 characters."})
    try:
        return create_user(email, password)
    except Exception as error:
        if "UNIQUE constraint" in str(error):
            return JSONResponse(status_code=409, content={"detail": "An account with this email already exists."})
        raise


@router.post("/auth/login", response_model=None)
async def login(email: str = Form(...), password: str = Form(...)):
    from backend.database.local_db import authenticate

    user, token = authenticate(email, password)
    if user is None:
        return JSONResponse(status_code=401, content={"detail": "Invalid email or password."})
    return {"user": user, "token": token}


@router.get("/auth/me", response_model=None)
async def me(authorization: str | None = Header(default=None)):
    user = _current_user(authorization)
    if user is None:
        return JSONResponse(status_code=401, content={"detail": "Authentication required."})
    return user


@router.post("/auth/logout")
async def logout(authorization: str | None = Header(default=None)):
    from backend.database.local_db import revoke_token

    token = authorization.removeprefix("Bearer ").strip() if authorization else None
    revoke_token(token)
    return {"status": "ok"}


@router.get("/")
async def root() -> dict[str, str]:
    return {"service": "ats-resume-analyzer", "status": "ok"}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/validate-upload")
async def validate_upload(file: UploadFile = File(...)) -> JSONResponse:
    from backend.services.resume_parser import validate_file

    file_data = await file.read()
    valid, message, mime_type = validate_file(file_data, file.filename or "")
    return JSONResponse(
        status_code=200 if valid else 400,
        content={"valid": valid, "message": message, "mime_type": mime_type},
    )


@router.post("/analyze", response_model=None)
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(""),
    authorization: str | None = Header(default=None),
) -> dict[str, object] | JSONResponse:
    from backend.services.resume_parser import (
        FileParsingError,
        TextExtractionError,
        extract_text,
        validate_file,
    )

    file_data = await file.read()
    filename = file.filename or "resume"
    valid, message, mime_type = validate_file(file_data, filename)
    if not valid:
        return JSONResponse(status_code=400, content={"detail": message})

    try:
        resume_text = extract_text(file_data, filename)
    except (FileParsingError, TextExtractionError) as error:
        return JSONResponse(status_code=400, content={"detail": str(error)})

    resume_words = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", resume_text.lower()))
    jd_words = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", job_description.lower()))
    ignored = {"and", "the", "with", "for", "you", "that", "this", "from", "are"}
    keywords = sorted(word for word in jd_words - ignored if len(word) > 2)
    matched = [word for word in keywords if word in resume_words]
    missing = [word for word in keywords if word not in resume_words]
    keyword_score = round((len(matched) / len(keywords) * 100) if keywords else 100, 1)
    content_score = min(100, round(len(resume_words) / 4, 1))
    ats_score = round(keyword_score * 0.7 + content_score * 0.3, 1)
    issues = [
        f"Missing job-description keywords: {', '.join(missing[:12])}."
        for missing in [missing]
        if missing
    ]
    if len(resume_text) < 300:
        issues.append("Resume text is very short; add measurable experience and achievements.")

    result = {
        "filename": filename,
        "mime_type": mime_type,
        "ats_score": ats_score,
        "keyword_match": keyword_score,
        "content_score": content_score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "issues": issues,
        "extracted_text_preview": resume_text[:500],
    }
    user = _current_user(authorization)
    if user:
        from backend.database.local_db import save_analysis

        result["analysis_id"] = save_analysis(user["id"], filename, job_description, result)
    return result


@router.get("/history", response_model=None)
async def history(authorization: str | None = Header(default=None)):
    user = _current_user(authorization)
    if user is None:
        return JSONResponse(status_code=401, content={"detail": "Authentication required."})
    from backend.database.local_db import list_analyses

    return {"items": list_analyses(user["id"])}


@router.get("/history/{analysis_id}/download")
async def download_analysis(analysis_id: int, authorization: str | None = Header(default=None)):
    user = _current_user(authorization)
    if user is None:
        return JSONResponse(status_code=401, content={"detail": "Authentication required."})
    from backend.database.local_db import get_analysis

    analysis = get_analysis(user["id"], analysis_id)
    if analysis is None:
        return JSONResponse(status_code=404, content={"detail": "Analysis not found."})
    report = {
        "filename": analysis["filename"],
        "created_at": analysis["created_at"],
        "job_description": analysis["job_description"],
        "result": analysis["result"],
    }
    return Response(
        content=json.dumps(report, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="ats-report-{analysis_id}.json"'},
    )