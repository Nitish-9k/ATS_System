# ATS Resume Scorer

## Run the API

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Check `http://localhost:8000/health` after startup. The API falls back to a
blank English spaCy pipeline when the optional models are not installed.
The Streamlit screen can submit a resume and job description to
`POST /analyze` for keyword matching and an ATS score.
Accounts, analysis history, and JSON report downloads are stored locally in
`backend/database/ats.db`; this file is created automatically on startup.

## Run the Streamlit UI

```powershell
streamlit run frontend/streamlit_app.py
```