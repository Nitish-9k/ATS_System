import os
import json

import requests
import streamlit as st


API_URL = os.getenv("ATS_API_URL", "http://localhost:8000").rstrip("/")
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None


def check_api() -> bool:
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        response.raise_for_status()
        return response.json().get("status") == "ok"
    except (requests.RequestException, ValueError):
        return False


def analyze_upload(uploaded_file, job_description: str) -> dict:
    response = requests.post(
        f"{API_URL}/analyze",
        files={
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type or "application/octet-stream",
            )
        },
        data={"job_description": job_description},
        headers={"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {},
        timeout=30,
    )
    try:
        payload = response.json()
    except ValueError:
        payload = {"message": response.text or "The API returned an invalid response."}
    if response.status_code >= 400:
        raise RuntimeError(payload.get("message", "Upload validation failed."))
    return payload


def api_request(method: str, path: str, **kwargs):
    headers = kwargs.pop("headers", {})
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    response = requests.request(method, f"{API_URL}{path}", headers=headers, timeout=15, **kwargs)
    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text}
    if response.status_code >= 400:
        raise RuntimeError(payload.get("detail", "Request failed."))
    return payload


st.set_page_config(page_title="ATS Resume Scorer", page_icon=":page_facing_up")
st.title("ATS Resume Scorer")

with st.sidebar:
    st.header("Account")
    if st.session_state.user:
        st.success(st.session_state.user["email"])
        if st.button("Sign out"):
            try:
                api_request("POST", "/auth/logout")
            except (requests.RequestException, RuntimeError):
                pass
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()
    else:
        auth_mode = st.radio("Choose action", ["Sign in", "Sign up"])
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button(auth_mode):
            try:
                path = "/auth/login" if auth_mode == "Sign in" else "/auth/signup"
                payload = api_request("POST", path, data={"email": email, "password": password})
                if auth_mode == "Sign up":
                    st.success("Account created. Sign in to continue.")
                else:
                    st.session_state.token = payload["token"]
                    st.session_state.user = payload["user"]
                    st.rerun()
            except (requests.RequestException, RuntimeError) as error:
                st.error(str(error))
    st.caption("History is available after signing in.")

st.caption("Upload a resume and compare it with a job description.")

if check_api():
    st.success("Backend connected")
else:
    st.error(
        f"Backend unavailable at {API_URL}. Start it with "
        "`python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`."
    )

uploaded_file = st.file_uploader(
    "Resume file",
    type=["pdf", "doc", "docx"],
    help="Maximum file size: 5 MB.",
)
job_description = st.text_area("Job description (optional)", height=180)

if st.button("Analyze resume", type="primary"):
    if uploaded_file is None:
        st.warning("Choose a PDF, DOC, or DOCX resume first.")
    else:
        try:
            result = analyze_upload(uploaded_file, job_description)
            st.metric("ATS score", f"{result['ats_score']}%")
            st.metric("Keyword match", f"{result['keyword_match']}%")
            st.metric("Content score", f"{result['content_score']}%")
            if result["matched_keywords"]:
                st.write("Matched keywords:", ", ".join(result["matched_keywords"]))
            if result["missing_keywords"]:
                st.warning("Missing keywords: " + ", ".join(result["missing_keywords"]))
            for issue in result["issues"]:
                st.error(issue)
            with st.expander("Extracted resume text"):
                st.write(result["extracted_text_preview"])
            st.download_button(
                "Download report",
                data=json.dumps(result, indent=2),
                file_name="ats-report.json",
                mime="application/json",
            )
        except (requests.RequestException, RuntimeError) as error:
            st.error(f"Could not validate the resume: {error}")

if st.session_state.user:
    st.divider()
    st.subheader("Analysis history")
    if st.button("Refresh history"):
        st.rerun()
    try:
        history_items = api_request("GET", "/history").get("items", [])
        if not history_items:
            st.info("No saved analyses yet.")
        for item in history_items:
            result = item["result"]
            with st.expander(f"{item['filename']} — {result['ats_score']}% — {item['created_at'][:19]}"):
                st.write(f"Keyword match: {result['keyword_match']}%")
                st.write(f"Missing keywords: {', '.join(result['missing_keywords']) or 'None'}")
                report = api_request("GET", f"/history/{item['id']}/download")
                st.download_button(
                    "Download saved report",
                    data=json.dumps(report, indent=2),
                    file_name=f"ats-report-{item['id']}.json",
                    mime="application/json",
                    key=f"download-{item['id']}",
                )
    except (requests.RequestException, RuntimeError) as error:
        st.error(f"Could not load history: {error}")