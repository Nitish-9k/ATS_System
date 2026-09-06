import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "ats.db"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                job_description TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )


def _password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def _password_matches(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$", 1)
    candidate = _password_hash(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(candidate.split("$", 1)[1], digest_hex)


def create_user(email: str, password: str) -> dict:
    init_db()
    with _connect() as connection:
        cursor = connection.execute(
            "INSERT INTO users(email, password_hash, created_at) VALUES (?, ?, ?)",
            (email.lower().strip(), _password_hash(password), datetime.now(timezone.utc).isoformat()),
        )
        return {"id": cursor.lastrowid, "email": email.lower().strip()}


def authenticate(email: str, password: str) -> tuple[dict | None, str | None]:
    init_db()
    with _connect() as connection:
        user = connection.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()
        if user is None or not _password_matches(password, user["password_hash"]):
            return None, None
        token = secrets.token_urlsafe(32)
        connection.execute(
            "INSERT INTO sessions(token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user["id"], datetime.now(timezone.utc).isoformat()),
        )
        return {"id": user["id"], "email": user["email"]}, token


def user_from_token(token: str | None) -> dict | None:
    if not token:
        return None
    init_db()
    with _connect() as connection:
        user = connection.execute(
            """
            SELECT users.id, users.email
            FROM sessions JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()
        return dict(user) if user else None


def revoke_token(token: str | None) -> None:
    if token:
        with _connect() as connection:
            connection.execute("DELETE FROM sessions WHERE token = ?", (token,))


def save_analysis(user_id: int, filename: str, job_description: str, result: dict) -> int:
    import json

    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO analyses(user_id, filename, job_description, result_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, filename, job_description, json.dumps(result), datetime.now(timezone.utc).isoformat()),
        )
        return int(cursor.lastrowid)


def list_analyses(user_id: int) -> list[dict]:
    import json

    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, filename, job_description, result_json, created_at FROM analyses WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    return [
        {**dict(row), "result": json.loads(row["result_json"])}
        for row in rows
    ]


def get_analysis(user_id: int, analysis_id: int) -> dict | None:
    return next((item for item in list_analyses(user_id) if item["id"] == analysis_id), None)
