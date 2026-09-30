import json
import os
import re
import shutil
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import bcrypt
import jwt
from typing import Any
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr


# ============================================================
# PYTHON PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# RAG + MATCHING + M3 AGENT IMPORTS
# ============================================================

from backend.rag.retriever import JobRetriever
from backend.matching.service import MatchingService
from backend.matching.job_loader import get_jobs_by_id, load_all_jobs
from backend.agents.skill_gap_agent import skill_gap_agent
from backend.agents.application_agent import application_agent
from backend.agents.interview_agent import interview_agent
from backend.agents.career_assistant import career_assistant


# ============================================================
# PATH CONFIGURATION
# ============================================================

DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DATABASE = DATA_DIR / "career_companion.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

def load_env():
    """
    Loads variables from backend/.env
    without requiring python-dotenv.
    """

    env_file = BASE_DIR / ".env"

    if not env_file.exists():
        print(".env file not found.")
        return

    for line in env_file.read_text(
        encoding="utf-8"
    ).splitlines():

        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" in line:
            key, value = line.split("=", 1)

            os.environ.setdefault(
                key.strip(),
                value.strip()
            )


load_env()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI Career Companion Agent",
    version="0.6.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SERVICES
# ============================================================

job_retriever = None
matching_service = None
JOB_CACHE = None
JOB_CACHE_BY_ID = {}


# ============================================================
# PYDANTIC MODELS
# ============================================================

class ProfileInput(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    location: str | None = None
    target_role: str | None = None
    linkedin_url: str | None = None


class JobSearchInput(BaseModel):
    query: str
    top_k: int = 5


class JobMatchInput(BaseModel):
    top_k: int = 5


class SkillGapInput(BaseModel):
    job_id: str | None = None
    job_title: str | None = None


class ResumeCustomizationInput(BaseModel):
    job_id: str | None = None
    job_title: str | None = None


class CoverLetterInput(BaseModel):
    job_id: str | None = None
    job_title: str | None = None


class InterviewPrepInput(BaseModel):
    job_id: str | None = None
    job_title: str | None = None


class MockInterviewStartInput(BaseModel):
    job_id: str | None = None
    job_title: str | None = None


class MockInterviewAnswerInput(BaseModel):
    interview_id: int
    question_index: int
    question_text: str
    category: str = "Technical"
    user_answer: str


# ============================================================
# M4.1 — APPLICATION TRACKING & MANAGEMENT MODELS
# ============================================================

VALID_APPLICATION_STATUSES = [
    "Saved",
    "Planning to apply",
    "Applied",
    "Application under review",
    "Shortlisted",
    "Interview scheduled",
    "Interview completed",
    "Offer received",
    "Rejected",
    "Withdrawn",
]


class ApplicationCreateInput(BaseModel):
    job_id: str | None = None
    company_name: str
    job_title: str
    job_description: str | None = None
    application_date: str | None = None
    deadline: str | None = None
    status: str = "Saved"
    interview_date: str | None = None
    interview_status: str | None = None
    notes: str | None = None
    follow_up_date: str | None = None
    customized_resume: Any | None = None
    cover_letter: Any | None = None


class ApplicationUpdateInput(BaseModel):
    company_name: str | None = None
    job_title: str | None = None
    job_description: str | None = None
    application_date: str | None = None
    deadline: str | None = None
    status: str | None = None
    interview_date: str | None = None
    interview_status: str | None = None
    notes: str | None = None
    follow_up_date: str | None = None
    customized_resume: Any | None = None
    cover_letter: Any | None = None


class CareerAssistantInput(BaseModel):
    profile_id: int | None = None
    job_id: str | None = None
    conversation_id: str | None = None
    message: str
    history: list[dict] = []


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def create_database():

    connection = get_connection()

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            location TEXT,
            target_role TEXT,
            linkedin_url TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY(user_id)
                REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT,
            size_bytes INTEGER,
            uploaded_at TEXT NOT NULL,
            extraction_json TEXT,
            extraction_method TEXT,
            FOREIGN KEY(profile_id)
                REFERENCES profiles(id)
        );

        CREATE TABLE IF NOT EXISTS skill_gaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            job_id TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(profile_id)
                REFERENCES profiles(id)
        );

        CREATE TABLE IF NOT EXISTS customized_resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            job_id TEXT NOT NULL,
            resume_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(profile_id)
                REFERENCES profiles(id)
        );

        CREATE TABLE IF NOT EXISTS cover_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            job_id TEXT NOT NULL,
            letter_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(profile_id)
                REFERENCES profiles(id)
        );

        CREATE TABLE IF NOT EXISTS interview_preps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            job_id TEXT NOT NULL,
            prep_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(profile_id)
                REFERENCES profiles(id)
        );

        CREATE TABLE IF NOT EXISTS mock_interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            job_id TEXT NOT NULL,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            status TEXT NOT NULL,
            questions_json TEXT NOT NULL,
            current_index INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(profile_id)
                REFERENCES profiles(id)
        );

        CREATE TABLE IF NOT EXISTS mock_interview_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id INTEGER NOT NULL,
            question_index INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            category TEXT NOT NULL,
            user_answer TEXT NOT NULL,
            evaluation_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(interview_id)
                REFERENCES mock_interviews(id)
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            job_id TEXT,
            conversation_id TEXT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            context_used_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(profile_id)
                REFERENCES profiles(id)
        );

        CREATE TABLE IF NOT EXISTS auth_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_jti TEXT NOT NULL,
            issued_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            revoked_at TEXT,
            FOREIGN KEY(user_id)
                REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            job_id TEXT,
            company_name TEXT NOT NULL,
            job_title TEXT NOT NULL,
            job_description TEXT,
            application_date TEXT NOT NULL,
            deadline TEXT,
            status TEXT NOT NULL DEFAULT 'Saved',
            interview_date TEXT,
            interview_status TEXT,
            notes TEXT,
            follow_up_date TEXT,
            customized_resume TEXT,
            cover_letter TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(profile_id)
                REFERENCES profiles(id)
        );
        """
    )

    profile_columns = connection.execute("PRAGMA table_info(profiles)").fetchall()
    if not any(column[1] == "user_id" for column in profile_columns):
        connection.execute("ALTER TABLE profiles ADD COLUMN user_id INTEGER")
    if not any(column[1] == "updated_at" for column in profile_columns):
        connection.execute("ALTER TABLE profiles ADD COLUMN updated_at TEXT")

    users_columns = connection.execute("PRAGMA table_info(users)").fetchall()
    if not any(column[1] == "full_name" for column in users_columns):
        connection.execute("ALTER TABLE users ADD COLUMN full_name TEXT NOT NULL DEFAULT ''")
    if not any(column[1] == "updated_at" for column in users_columns):
        connection.execute("ALTER TABLE users ADD COLUMN updated_at TEXT")
    if not any(column[1] == "is_active" for column in users_columns):
        connection.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")

    columns = connection.execute("PRAGMA table_info(chat_messages)").fetchall()
    has_conversation_id = any(column[1] == "conversation_id" for column in columns)
    if not has_conversation_id:
        connection.execute("ALTER TABLE chat_messages ADD COLUMN conversation_id TEXT")

    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_profile_conversation ON chat_messages(profile_id, conversation_id, created_at)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_applications_profile ON applications(profile_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(profile_id, status)"
    )

    app_columns = connection.execute("PRAGMA table_info(applications)").fetchall()
    app_col_names = [column[1] for column in app_columns]
    for col_name, col_type in [
        ("job_id", "TEXT"),
        ("job_description", "TEXT"),
        ("deadline", "TEXT"),
        ("interview_date", "TEXT"),
        ("interview_status", "TEXT"),
        ("notes", "TEXT"),
        ("follow_up_date", "TEXT"),
        ("customized_resume", "TEXT"),
        ("cover_letter", "TEXT"),
    ]:
        if app_col_names and col_name not in app_col_names:
            connection.execute(f"ALTER TABLE applications ADD COLUMN {col_name} {col_type}")

    connection.execute("UPDATE profiles SET user_id = NULL WHERE user_id = 0")

    for row in connection.execute("SELECT id, email, full_name FROM profiles WHERE user_id IS NULL AND email IS NOT NULL").fetchall():
        match_user = connection.execute(
            "SELECT id FROM users WHERE email = ? LIMIT 1",
            (row["email"],)
        ).fetchone()
        if match_user:
            connection.execute(
                "UPDATE profiles SET user_id = ?, full_name = ?, updated_at = ? WHERE id = ?",
                (match_user["id"], row["full_name"], datetime.now(timezone.utc).isoformat(), row["id"])
            )

    connection.commit()
    connection.close()


# ============================================================
# AUTH HELPERS
# ============================================================

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "career-companion-dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_TTL_SECONDS = 60 * 60 * 24


class AuthRegisterInput(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str


class AuthLoginInput(BaseModel):
    email: EmailStr
    password: str


class AuthProfileInput(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    location: str | None = None
    target_role: str | None = None
    linkedin_url: str | None = None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: int) -> str:
    issued_at = int(time.time())
    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": issued_at + JWT_TTL_SECONDS,
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    connection = get_connection()
    connection.execute(
        """
        INSERT INTO auth_sessions (user_id, token_jti, issued_at, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            payload["jti"],
            datetime.fromtimestamp(issued_at, tz=timezone.utc).isoformat(),
            datetime.fromtimestamp(payload["exp"], tz=timezone.utc).isoformat(),
        )
    )
    connection.commit()
    connection.close()
    return token


def get_optional_current_user(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return None

    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required.")

    token = parts[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required.")

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed or token expired.")

    user_id = int(payload.get("sub", "0"))
    jti = payload.get("jti")

    connection = get_connection()
    user = connection.execute(
        "SELECT * FROM users WHERE id = ? AND is_active = 1",
        (user_id,)
    ).fetchone()
    if not user:
        connection.close()
        raise HTTPException(status_code=401, detail="User account not found.")

    if jti:
        session = connection.execute(
            "SELECT id FROM auth_sessions WHERE user_id = ? AND token_jti = ? AND revoked_at IS NULL",
            (user_id, jti)
        ).fetchone()
        if not session:
            connection.close()
            raise HTTPException(status_code=401, detail="Session expired or revoked.")

    connection.close()
    return dict(user)


def get_current_user(request: Request):
    user = get_optional_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


def safe_user_payload(user_row):
    if user_row is None:
        return None
    return {
        "id": user_row["id"],
        "email": user_row["email"],
        "full_name": user_row["full_name"],
        "created_at": user_row["created_at"],
        "updated_at": user_row["updated_at"],
        "is_active": bool(user_row["is_active"]),
    }


def get_profile_for_user(user_id: int):
    connection = get_connection()
    profile = connection.execute(
        "SELECT * FROM profiles WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    connection.close()
    return dict(profile) if profile else None


def ensure_user_profile(user_id: int, full_name: str, email: str):
    connection = get_connection()
    profile = connection.execute(
        "SELECT * FROM profiles WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,)
    ).fetchone()

    if profile is None:
        profile = connection.execute(
            "SELECT * FROM profiles WHERE email = ? ORDER BY id DESC LIMIT 1",
            (email,)
        ).fetchone()

    if profile is not None:
        connection.execute(
            "UPDATE profiles SET user_id = ?, full_name = ?, email = ?, updated_at = ? WHERE id = ?",
            (user_id, full_name, email, datetime.now(timezone.utc).isoformat(), profile["id"])
        )
        connection.commit()
        profile = connection.execute("SELECT * FROM profiles WHERE id = ?", (profile["id"],)).fetchone()
        connection.close()
        return dict(profile)

    now = datetime.now(timezone.utc).isoformat()
    cursor = connection.execute(
        """
        INSERT INTO profiles (user_id, full_name, email, phone, location, target_role, linkedin_url, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, full_name, email, None, None, None, None, now, now)
    )
    connection.commit()
    profile = connection.execute("SELECT * FROM profiles WHERE id = ?", (cursor.lastrowid,)).fetchone()
    connection.close()
    return dict(profile)


def assert_profile_access(profile_id: int, current_user: dict | None):
    if current_user is None:
        return

    connection = get_connection()
    profile = connection.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()

    if not profile:
        connection.close()
        raise HTTPException(status_code=404, detail="Profile not found.")

    if profile["user_id"] is None:
        if profile["email"] == current_user["email"]:
            connection.execute(
                "UPDATE profiles SET user_id = ?, updated_at = ? WHERE id = ?",
                (current_user["id"], datetime.now(timezone.utc).isoformat(), profile_id)
            )
            connection.commit()
            connection.close()
            return
        connection.close()
        raise HTTPException(status_code=403, detail="You do not have permission to access this profile.")

    if profile["user_id"] != current_user["id"]:
        connection.close()
        raise HTTPException(status_code=403, detail="You do not have permission to access this profile.")

    connection.close()


@app.post("/auth/register")
def register_user(request: AuthRegisterInput):
    full_name = (request.full_name or "").strip()
    if not full_name:
        raise HTTPException(status_code=422, detail="Please enter your name.")
    if len(request.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters.")
    if request.password != request.confirm_password:
        raise HTTPException(status_code=422, detail="Passwords do not match.")

    connection = get_connection()
    existing = connection.execute("SELECT id FROM users WHERE email = ?", (str(request.email).lower(),)).fetchone()
    connection.close()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    now = datetime.now(timezone.utc).isoformat()
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            INSERT INTO users (email, password_hash, full_name, created_at, updated_at, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (str(request.email).lower(), hash_password(request.password), full_name, now, now)
        )
        connection.commit()
        user_id = cursor.lastrowid
        user_row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        connection.close()

    profile = ensure_user_profile(user_id, full_name, str(request.email).lower())
    token = create_access_token(user_id)

    return {
        "token": token,
        "user": safe_user_payload(user_row),
        "profile": profile,
        "message": "Account created successfully."
    }


@app.post("/auth/login")
def login_user(request: AuthLoginInput):
    email = str(request.email).lower()
    connection = get_connection()
    user = connection.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email,)).fetchone()
    connection.close()

    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")

    token = create_access_token(user["id"])
    profile = get_profile_for_user(user["id"])
    if profile is None:
        profile = ensure_user_profile(user["id"], user["full_name"], email)

    return {
        "token": token,
        "user": safe_user_payload(user),
        "profile": profile,
        "message": "Login successful."
    }


@app.post("/auth/logout")
def logout_user(request: Request):
    current_user = get_current_user(request)
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ", 1)[1].strip() if auth_header.startswith("Bearer ") else ""
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            jti = payload.get("jti")
            if jti:
                connection = get_connection()
                connection.execute(
                    "UPDATE auth_sessions SET revoked_at = ? WHERE user_id = ? AND token_jti = ? AND revoked_at IS NULL",
                    (datetime.now(timezone.utc).isoformat(), current_user["id"], jti)
                )
                connection.commit()
                connection.close()
        except Exception:
            pass
    return {"message": "Logged out successfully."}


@app.get("/auth/me")
def get_current_auth_profile(request: Request):
    current_user = get_current_user(request)
    profile = get_profile_for_user(current_user["id"])
    if profile is None:
        profile = ensure_user_profile(current_user["id"], current_user["full_name"], current_user["email"])
    return {
        "user": safe_user_payload(current_user),
        "profile": profile,
    }


@app.put("/auth/profile")
def update_current_profile(request: Request, payload: AuthProfileInput):
    current_user = get_current_user(request)
    connection = get_connection()
    profile = connection.execute(
        "SELECT * FROM profiles WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (current_user["id"],)
    ).fetchone()

    if profile is None:
        profile = connection.execute(
            "SELECT * FROM profiles WHERE email = ? ORDER BY id DESC LIMIT 1",
            (current_user["email"],)
        ).fetchone()

    if profile is None:
        connection.close()
        profile = ensure_user_profile(current_user["id"], current_user["full_name"], current_user["email"])
        connection = get_connection()
        profile = connection.execute("SELECT * FROM profiles WHERE user_id = ? ORDER BY id DESC LIMIT 1", (current_user["id"],)).fetchone()

    update_map = {
        "full_name": payload.full_name or profile["full_name"],
        "email": str(payload.email or profile["email"]).lower(),
        "phone": payload.phone if payload.phone is not None else profile["phone"],
        "location": payload.location if payload.location is not None else profile["location"],
        "target_role": payload.target_role if payload.target_role is not None else profile["target_role"],
        "linkedin_url": payload.linkedin_url if payload.linkedin_url is not None else profile["linkedin_url"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    connection.execute(
        """
        UPDATE profiles
        SET full_name = ?, email = ?, phone = ?, location = ?, target_role = ?, linkedin_url = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            update_map["full_name"],
            update_map["email"],
            update_map["phone"],
            update_map["location"],
            update_map["target_role"],
            update_map["linkedin_url"],
            update_map["updated_at"],
            profile["id"],
        )
    )

    connection.execute(
        "UPDATE users SET full_name = ?, email = ?, updated_at = ? WHERE id = ?",
        (update_map["full_name"], update_map["email"], update_map["updated_at"], current_user["id"])
    )
    connection.commit()
    updated = connection.execute("SELECT * FROM profiles WHERE id = ?", (profile["id"],)).fetchone()
    connection.close()
    return {"message": "Profile updated successfully.", "profile": dict(updated)}


@app.get("/profiles/{profile_id}")
def get_profile_by_id(profile_id: int, request: Request):
    current_user = get_optional_current_user(request)
    if current_user is not None:
        assert_profile_access(profile_id, current_user)

    connection = get_connection()
    profile = connection.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    connection.close()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return dict(profile)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def initialize_services():

    global job_retriever
    global matching_service

    print("\n" + "=" * 60)
    print("INITIALIZING AI CAREER COMPANION BACKEND")
    print("=" * 60)

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    create_database()

    print("\nDatabase initialized successfully.")

    # --------------------------------------------------------
    # RAG Retriever
    # --------------------------------------------------------

    try:

        print("\nLoading RAG job retriever...")

        job_retriever = JobRetriever()

        print(
            "RAG retriever initialized successfully."
        )

    except Exception as error:

        job_retriever = None

        print(
            f"WARNING: RAG retriever could not be initialized: {error}"
        )

        print(
            "Semantic job search will be unavailable."
        )

    # --------------------------------------------------------
    # Matching Service
    # --------------------------------------------------------

    try:

        print("\nLoading Job-Resume Matching Service...")

        matching_service = MatchingService(job_retriever)

        print(
            "Job-Resume Matching Service initialized successfully."
        )

    except Exception as error:

        matching_service = None

        print(
            f"WARNING: Matching service could not be initialized: {error}"
        )

        print(
            "Job matching will be unavailable."
        )

    print("\nBackend initialization complete.")
    print("=" * 60)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "ok",
        "rag_available": job_retriever is not None,
        "matching_available": matching_service is not None
    }


# ============================================================
# CREATE PROFILE
# ============================================================

@app.post("/profiles")
def create_profile(profile: ProfileInput, request: Request):
    current_user = None
    try:
        current_user = get_optional_current_user(request)
    except HTTPException:
        current_user = None

    connection = get_connection()
    existing = connection.execute(
        """
        SELECT *
        FROM profiles
        WHERE email = ?
        """,
        (
            str(profile.email).lower(),
        )
    ).fetchone()

    if current_user is not None:
        if existing and existing["user_id"] not in (None, current_user["id"]):
            connection.close()
            raise HTTPException(status_code=403, detail="You do not have permission to access this profile.")
        if existing and existing["user_id"] is None:
            connection.execute(
                "UPDATE profiles SET user_id = ?, full_name = ?, updated_at = ? WHERE id = ?",
                (current_user["id"], profile.full_name, datetime.now(timezone.utc).isoformat(), existing["id"])
            )
            connection.commit()
            profile_row = connection.execute("SELECT * FROM profiles WHERE id = ?", (existing["id"],)).fetchone()
            connection.close()
            return dict(profile_row)

    if existing:
        connection.close()
        return dict(existing)

    now = datetime.now(timezone.utc).isoformat()

    try:
        if current_user is not None:
            cursor = connection.execute(
                """
                INSERT INTO profiles
                (
                    user_id,
                    full_name,
                    email,
                    phone,
                    location,
                    target_role,
                    linkedin_url,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    current_user["id"],
                    profile.full_name,
                    str(profile.email).lower(),
                    profile.phone,
                    profile.location,
                    profile.target_role,
                    profile.linkedin_url,
                    now,
                    now,
                )
            )
        else:
            cursor = connection.execute(
                """
                INSERT INTO profiles
                (
                    full_name,
                    email,
                    phone,
                    location,
                    target_role,
                    linkedin_url,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.full_name,
                    str(profile.email).lower(),
                    profile.phone,
                    profile.location,
                    profile.target_role,
                    profile.linkedin_url,
                    now,
                    now,
                )
            )

        connection.commit()

        saved_profile = connection.execute(
            """
            SELECT *
            FROM profiles
            WHERE id = ?
            """,
            (
                cursor.lastrowid,
            )
        ).fetchone()

        return dict(saved_profile)

    finally:
        connection.close()


# ============================================================
# RESUME TEXT EXTRACTION
# ============================================================

def extract_text(file_path: Path):

    suffix = file_path.suffix.lower()

    # --------------------------------------------------------
    # TXT
    # --------------------------------------------------------

    if suffix == ".txt":

        return file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    if suffix == ".pdf":

        try:

            from pypdf import PdfReader

            reader = PdfReader(
                str(file_path)
            )

            pages = []

            for page in reader.pages:

                text = page.extract_text()

                if text:
                    pages.append(text)

            return "\n".join(pages)

        except Exception as error:

            raise RuntimeError(
                f"PDF extraction failed: {error}"
            )

    # --------------------------------------------------------
    # DOCX
    # --------------------------------------------------------

    if suffix == ".docx":

        try:

            from docx import Document

            document = Document(
                str(file_path)
            )

            paragraphs = [
                paragraph.text
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            ]

            return "\n".join(paragraphs)

        except Exception as error:

            raise RuntimeError(
                f"DOCX extraction failed: {error}"
            )

    raise ValueError(
        "Unsupported file type. Use PDF, DOCX or TXT."
    )


# ============================================================
# LOCAL RESUME EXTRACTION FALLBACK
# ============================================================

def local_resume_extraction(text: str):

    clean_text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    lower_text = clean_text.lower()

    # --------------------------------------------------------
    # Skills
    # --------------------------------------------------------

    known_skills = [
        "python",
        "java",
        "c",
        "c++",
        "javascript",
        "typescript",
        "html",
        "css",
        "react",
        "node.js",
        "sql",
        "mongodb",
        "nosql",
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "pandas",
        "numpy",
        "opencv",
        "nlp",
        "computer vision",
        "git",
        "github",
        "fastapi",
        "flask",
        "streamlit",
        "docker",
        "aws",
        "azure",
        "gcp",
        "firebase",
        "linux",
        "data analysis",
        "data science"
    ]

    skills = []

    for skill in known_skills:

        if skill.lower() in lower_text:

            skills.append(skill)

    # --------------------------------------------------------
    # Education
    # --------------------------------------------------------

    education = []

    education_patterns = [
        r"(B\.?E\.?.{0,120})",
        r"(B\.?Tech\.?.{0,120})",
        r"(Bachelor.{0,120})",
        r"(M\.?Tech\.?.{0,120})",
        r"(Master.{0,120})",
        r"(B\.?Sc\.?.{0,120})",
        r"(M\.?Sc\.?.{0,120})",
        r"(Ph\.?D\.?.{0,120})"
    ]

    for pattern in education_patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        education.extend(
            matches[:3]
        )

    education = list(
        dict.fromkeys(
            item.strip()
            for item in education
            if item.strip()
        )
    )

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    experience = []

    experience_keywords = [
        "internship",
        "intern",
        "experience",
        "developer",
        "engineer",
        "analyst",
        "research"
    ]

    for keyword in experience_keywords:

        if keyword in lower_text:

            experience.append(
                keyword.title()
            )

    # --------------------------------------------------------
    # Projects
    # --------------------------------------------------------

    projects = []

    project_match = re.search(
        r"(projects?)(.*?)(certifications?|education|experience|skills|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    if project_match:

        project_text = project_match.group(2).strip()

        if project_text:

            projects.append(
                project_text[:1000]
            )

    # --------------------------------------------------------
    # Certifications
    # --------------------------------------------------------

    certifications = []

    certification_match = re.search(
        r"(certifications?|courses?)(.*?)(projects?|education|experience|skills|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    if certification_match:

        certification_text = (
            certification_match
            .group(2)
            .strip()
        )

        if certification_text:

            certifications.append(
                certification_text[:1000]
            )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = clean_text[:1000]

    return {
        "summary": summary,
        "skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects,
        "certifications": certifications
    }


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_gemini_client():

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    from google import genai

    return genai.Client(
        api_key=api_key
    )


# ============================================================
# GEMINI MODEL NAME
# ============================================================

def get_gemini_model():

    return os.getenv(
        "GEMINI_MODEL",
        "gemini-3.6-flash"
    )


# ============================================================
# CLEAN GEMINI JSON
# ============================================================

def clean_gemini_json(raw_text: str):

    raw_text = raw_text.strip()

    # Remove markdown code fences

    raw_text = re.sub(
        r"^```(?:json)?\s*",
        "",
        raw_text,
        flags=re.IGNORECASE
    )

    raw_text = re.sub(
        r"\s*```$",
        "",
        raw_text
    )

    return raw_text.strip()


# ============================================================
# GEMINI RESUME EXTRACTION
# ============================================================

def gemini_resume_extraction(text: str):

    client = get_gemini_client()
    model_name = get_gemini_model()

    prompt = f"""
You are a resume information extraction system.

Analyze the following resume and return ONLY valid JSON.

Required JSON structure:

{{
  "summary": "short professional summary",
  "skills": [],
  "education": [],
  "experience": [],
  "projects": [],
  "certifications": []
}}

Rules:

- skills must be a list of skills.
- education must contain educational qualifications.
- experience must contain internships/jobs/research experience.
- projects must contain project names or descriptions.
- certifications must contain certifications/courses.
- Do not invent information.
- If a section is unavailable, return an empty list.
- Return JSON only.

RESUME:

{text[:20000]}
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )

    raw_text = (
        response.text
        if response and response.text
        else ""
    ).strip()

    if not raw_text:

        raise RuntimeError(
            "Gemini returned an empty response."
        )

    raw_text = clean_gemini_json(
        raw_text
    )

    parsed = json.loads(
        raw_text
    )

    return parsed


# ============================================================
# GEMINI MATCH EXPLANATION
# ============================================================

def gemini_match_explanations(
    candidate: dict,
    results: list
):

    """
    Generate personalized natural-language explanations
    for job matches using Gemini.

    Gemini does NOT calculate the match score.

    The deterministic matching service calculates:

    - match_score
    - matched_skills
    - missing_skills
    - qualification scores
    - retrieval similarity

    Gemini only explains those results.
    """

    if not results:

        return {}

    client = get_gemini_client()
    model_name = get_gemini_model()

    # --------------------------------------------------------
    # Candidate evidence
    # --------------------------------------------------------

    candidate_evidence = {
        "name": candidate.get("full_name"),
        "target_role": candidate.get("target_role"),
        "skills": candidate.get("skills", []),
        "education": candidate.get("education", []),
        "experience": candidate.get("experience", []),
        "projects": candidate.get("projects", []),
        "certifications": candidate.get("certifications", [])
    }

    # --------------------------------------------------------
    # Job matching evidence
    # --------------------------------------------------------

    job_evidence = []

    for index, result in enumerate(results):

        evidence = {}

        for key, value in result.items():

            if key.lower() in {
                "reasoning",
                "explanation",
                "why_this_match"
            }:
                continue

            if key in {
                "job_id",
                "job_title",
                "company",
                "location",
                "work_type",
                "description",
                "required_skills",
                "preferred_skills",
                "matched_skills",
                "missing_skills",
                "match_score",
                "required_skill_score",
                "preferred_skill_score",
                "project_score",
                "education_score",
                "experience_score",
                "qualification_score",
                "retrieval_similarity"
            }:

                evidence[key] = value

        evidence["_result_index"] = index

        job_evidence.append(
            evidence
        )

    prompt = f"""
You are an AI career advisor.

Your task is to explain why each recommended job
matches the candidate based ONLY on the supplied evidence.

IMPORTANT:

1. Do NOT calculate or modify the match score.
2. Do NOT invent candidate skills.
3. Do NOT invent job requirements.
4. Use ONLY the candidate information and matching evidence supplied below.
5. Mention strong skill alignment when appropriate.
6. Mention relevant projects or education when supported.
7. Mention important missing skills when present.
8. Be honest about weaknesses.
9. Do not say the candidate is "perfect" unless the evidence genuinely supports it.
10. Each explanation should be personalized.
11. Each explanation should be 2-4 sentences.
12. Return ONLY valid JSON.
13. The JSON must contain an array called "explanations".
14. Each explanation must contain:
    - "result_index"
    - "job_id"
    - "reasoning"

Required format:

{{
  "explanations": [
    {{
      "result_index": 0,
      "job_id": "JOB001",
      "reasoning": "..."
    }}
  ]
}}

CANDIDATE:

{json.dumps(
    candidate_evidence,
    ensure_ascii=False,
    indent=2
)}

MATCHING EVIDENCE:

{json.dumps(
    job_evidence,
    ensure_ascii=False,
    indent=2
)}
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )

    raw_text = (
        response.text
        if response and response.text
        else ""
    ).strip()

    if not raw_text:

        raise RuntimeError(
            "Gemini returned an empty match explanation."
        )

    raw_text = clean_gemini_json(
        raw_text
    )

    parsed = json.loads(
        raw_text
    )

    explanations = {}

    for item in parsed.get(
        "explanations",
        []
    ):

        result_index = item.get(
            "result_index"
        )

        job_id = item.get(
            "job_id"
        )

        reasoning = item.get(
            "reasoning"
        )

        if reasoning:

            if job_id is not None:

                key = str(job_id)

            else:

                key = str(result_index)

            explanations[key] = reasoning

    return explanations


# ============================================================
# RESUME UPLOAD + ANALYSIS
# ============================================================

@app.post("/profiles/{profile_id}/resumes")
async def upload_resume(
    profile_id: int,
    request: Request,
    file: UploadFile = File(...)
):
    current_user = get_optional_current_user(request)
    if current_user is not None:
        assert_profile_access(profile_id, current_user)

    # --------------------------------------------------------
    # Validate profile
    # --------------------------------------------------------

    connection = get_connection()

    profile = connection.execute(
        """
        SELECT *
        FROM profiles
        WHERE id = ?
        """,
        (profile_id,)
    ).fetchone()

    connection.close()

    if not profile:

        raise HTTPException(
            status_code=404,
            detail="Profile not found."
        )

    # --------------------------------------------------------
    # Validate file type
    # --------------------------------------------------------

    allowed_extensions = {
        ".pdf",
        ".docx",
        ".txt"
    }

    extension = Path(
        file.filename or ""
    ).suffix.lower()

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX and TXT files are supported."
        )

    # --------------------------------------------------------
    # Save file
    # --------------------------------------------------------

    safe_filename = Path(
        file.filename or "resume"
    ).name

    timestamp = int(
        time.time()
    )

    saved_filename = (
        f"{profile_id}_{timestamp}_{safe_filename}"
    )

    saved_path = (
        UPLOAD_DIR /
        saved_filename
    )

    try:

        with saved_path.open(
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Could not save resume: {error}"
        )

    # --------------------------------------------------------
    # Extract raw text
    # --------------------------------------------------------

    try:

        resume_text = extract_text(
            saved_path
        )

    except Exception as error:

        if saved_path.exists():
            saved_path.unlink()

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    if not resume_text.strip():

        if saved_path.exists():
            saved_path.unlink()

        raise HTTPException(
            status_code=400,
            detail="Could not extract text from the uploaded resume."
        )

    # --------------------------------------------------------
    # AI extraction
    # --------------------------------------------------------

    extraction_method = "local_fallback"

    try:

        extracted = gemini_resume_extraction(
            resume_text
        )

        extraction_method = "gemini_llm"

        print(
            "Gemini resume extraction successful."
        )

    except Exception as error:

        print(
            "Gemini extraction failed."
        )

        print(
            f"Reason: {error}"
        )

        print(
            "Using local resume extraction fallback."
        )

        extracted = local_resume_extraction(
            resume_text
        )

        extraction_method = "local_fallback"

    # --------------------------------------------------------
    # Save extraction
    # --------------------------------------------------------

    uploaded_at = datetime.now(
        timezone.utc
    ).isoformat()

    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            INSERT INTO resumes
            (
                profile_id,
                filename,
                file_path,
                file_type,
                size_bytes,
                uploaded_at,
                extraction_json,
                extraction_method
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                safe_filename,
                str(saved_path),
                extension,
                saved_path.stat().st_size,
                uploaded_at,
                json.dumps(
                    extracted,
                    ensure_ascii=False
                ),
                extraction_method
            )
        )

        connection.commit()

        resume_id = cursor.lastrowid

    finally:

        connection.close()

    return {
        "status": "success",
        "resume_id": resume_id,
        "profile_id": profile_id,
        "filename": safe_filename,
        "extraction_method": extraction_method,
        "extracted_profile": extracted
    }


# ============================================================
# GET LATEST RESUME
# ============================================================

@app.get("/profiles/{profile_id}/resumes/latest")
def get_latest_resume(profile_id: int, request: Request):
    current_user = get_optional_current_user(request)
    if current_user is not None:
        assert_profile_access(profile_id, current_user)

    connection = get_connection()

    resume = connection.execute(
        """
        SELECT *
        FROM resumes
        WHERE profile_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (profile_id,)
    ).fetchone()

    connection.close()

    if not resume:

        raise HTTPException(
            status_code=404,
            detail="No resume found for this profile."
        )

    result = dict(resume)

    if result.get("extraction_json"):

        try:

            result["extracted_profile"] = json.loads(
                result["extraction_json"]
            )

        except Exception:

            result["extracted_profile"] = {}

    result.pop(
        "extraction_json",
        None
    )

    return result


# ============================================================
# JOB SEARCH
# ============================================================

@app.post("/jobs/search")
def search_jobs(request: JobSearchInput):

    if job_retriever is None:

        raise HTTPException(
            status_code=503,
            detail="RAG job retriever is unavailable."
        )

    if request.top_k < 1:

        raise HTTPException(
            status_code=400,
            detail="top_k must be at least 1."
        )

    try:

        results = job_retriever.search(
            request.query,
            top_k=request.top_k
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Job search failed: {error}"
        )

    return {
        "query": request.query,
        "results": results
    }


# ============================================================
# JOB MATCHING
# ============================================================

@app.post("/profiles/{profile_id}/job-matches")
def get_job_matches(
    profile_id: int,
    request: JobMatchInput,
    auth_request: Request
):
    current_user = get_optional_current_user(auth_request)
    if current_user is not None:
        assert_profile_access(profile_id, current_user)

    if matching_service is None:

        raise HTTPException(
            status_code=503,
            detail="Matching service is unavailable."
        )

    if request.top_k < 1:

        raise HTTPException(
            status_code=400,
            detail="top_k must be at least 1."
        )

    # --------------------------------------------------------
    # Get profile
    # --------------------------------------------------------

    connection = get_connection()

    profile = connection.execute(
        """
        SELECT *
        FROM profiles
        WHERE id = ?
        """,
        (profile_id,)
    ).fetchone()

    if not profile:

        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Profile not found."
        )

    # --------------------------------------------------------
    # Get latest resume
    # --------------------------------------------------------

    resume = connection.execute(
        """
        SELECT *
        FROM resumes
        WHERE profile_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (profile_id,)
    ).fetchone()

    connection.close()

    if not resume:

        raise HTTPException(
            status_code=404,
            detail="Please upload a resume before requesting job matches."
        )

    # --------------------------------------------------------
    # Build candidate
    # --------------------------------------------------------

    candidate = dict(profile)

    extraction = {}

    if resume["extraction_json"]:

        try:

            extraction = json.loads(
                resume["extraction_json"]
            )

        except Exception:

            extraction = {}

    candidate.update(
        extraction
    )

    # --------------------------------------------------------
    # Deterministic matching
    # --------------------------------------------------------

    try:

        results = matching_service.match_candidate(
            candidate,
            top_k=request.top_k
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Job matching failed: {error}"
        )

    # --------------------------------------------------------
    # Gemini explanation layer
    # --------------------------------------------------------

    explanation_source = "gemini_llm"

    try:

        explanations = gemini_match_explanations(
            candidate,
            results
        )

        print(
            f"Gemini generated explanations for "
            f"{len(explanations)} job matches."
        )

    except Exception as error:

        print(
            "Gemini match explanation failed."
        )

        print(
            f"Reason: {error}"
        )

        explanations = {}

        explanation_source = "unavailable"

    # --------------------------------------------------------
    # Attach explanations
    # --------------------------------------------------------

    final_results = []

    for index, result in enumerate(results):

        result_copy = dict(result)

        job_id = result_copy.get(
            "job_id"
        )

        explanation = None

        # First try exact job_id

        if job_id is not None:

            explanation = explanations.get(
                str(job_id)
            )

        # Fallback to result index

        if not explanation:

            explanation = explanations.get(
                str(index)
            )

        if explanation:

            result_copy["reasoning"] = explanation
            result_copy["reasoning_source"] = "gemini_llm"

        else:

            result_copy["reasoning"] = (
                "AI explanation is currently unavailable for this match."
            )

            result_copy["reasoning_source"] = "unavailable"

        final_results.append(
            result_copy
        )

    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    return {
        "profile_id": profile_id,
        "results": final_results,
        "reasoning_source": explanation_source
    }


# ============================================================
# HELPER: CACHED DATA
# ============================================================

def get_cached_jobs():
    global JOB_CACHE, JOB_CACHE_BY_ID

    if JOB_CACHE is None:
        JOB_CACHE = load_all_jobs()
        JOB_CACHE_BY_ID = {
            str(job.get("job_id")): job
            for job in JOB_CACHE
            if job.get("job_id") is not None
        }

    return JOB_CACHE


# ============================================================
# HELPER: RESOLVE CANDIDATE & JOB DATA
# ============================================================

def resolve_candidate_and_job(
    profile_id: int,
    job_id: str | None = None,
    job_title: str | None = None,
    current_user: dict | None = None
):
    """
    Loads verified candidate profile and resolves target job from dataset or matches.
    """
    assert_profile_access(profile_id, current_user)

    connection = get_connection()

    profile_row = connection.execute(
        """
        SELECT *
        FROM profiles
        WHERE id = ?
        """,
        (profile_id,)
    ).fetchone()

    if not profile_row:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="Profile not found."
        )

    resume_row = connection.execute(
        """
        SELECT *
        FROM resumes
        WHERE profile_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (profile_id,)
    ).fetchone()

    connection.close()

    if not resume_row:
        raise HTTPException(
            status_code=404,
            detail="Please upload a resume before using Milestone 3 AI features."
        )

    candidate = dict(profile_row)

    if resume_row["extraction_json"]:
        try:
            extraction = json.loads(resume_row["extraction_json"])
            candidate.update(extraction)
        except Exception:
            pass

    # Resolve job using cached dataset
    all_jobs = get_cached_jobs()
    selected_job = None

    if job_id:
        selected_job = JOB_CACHE_BY_ID.get(str(job_id))
    elif job_title:
        for j in all_jobs:
            if (
                j.get("job_title")
                and j.get("job_title").strip().lower() == job_title.strip().lower()
            ):
                selected_job = j
                break

    # Fallback to first job if none specified
    if selected_job is None and all_jobs:
        selected_job = all_jobs[0]

    if selected_job is None:
        raise HTTPException(
            status_code=404,
            detail="Target job could not be resolved from dataset."
        )

    return candidate, selected_job


# ============================================================
# M3.1 — SKILL GAP ANALYSIS
# ============================================================

@app.post("/profiles/{profile_id}/skill-gap")
def analyze_skill_gap(
    profile_id: int,
    request: SkillGapInput,
    auth_request: Request
):
    current_user = get_optional_current_user(auth_request)
    candidate, job = resolve_candidate_and_job(
        profile_id=profile_id,
        job_id=request.job_id,
        job_title=request.job_title,
        current_user=current_user
    )

    result = skill_gap_agent.analyze_skill_gap(
        candidate=candidate,
        job=job
    )

    # Persist analysis
    now = datetime.now(timezone.utc).isoformat()
    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO skill_gaps (profile_id, job_id, result_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                profile_id,
                str(job.get("job_id", "")),
                json.dumps(result, ensure_ascii=False),
                now
            )
        )
        connection.commit()
    finally:
        connection.close()

    result["profile_id"] = profile_id
    result["job_id"] = job.get("job_id")
    return result


# ============================================================
# M3.2 — RESUME CUSTOMIZATION
# ============================================================

@app.post("/profiles/{profile_id}/customize-resume")
def customize_resume(
    profile_id: int,
    request: ResumeCustomizationInput,
    auth_request: Request
):
    current_user = get_optional_current_user(auth_request)
    candidate, job = resolve_candidate_and_job(
        profile_id=profile_id,
        job_id=request.job_id,
        job_title=request.job_title,
        current_user=current_user
    )

    result = application_agent.customize_resume(
        candidate=candidate,
        job=job
    )

    now = datetime.now(timezone.utc).isoformat()
    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO customized_resumes (profile_id, job_id, resume_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                profile_id,
                str(job.get("job_id", "")),
                json.dumps(result, ensure_ascii=False),
                now
            )
        )
        connection.commit()
    finally:
        connection.close()

    result["profile_id"] = profile_id
    result["job_id"] = job.get("job_id")
    return result


# ============================================================
# M3.2 — COVER LETTER GENERATION
# ============================================================

@app.post("/profiles/{profile_id}/cover-letter")
def generate_cover_letter(
    profile_id: int,
    request: CoverLetterInput,
    auth_request: Request
):
    current_user = get_optional_current_user(auth_request)
    candidate, job = resolve_candidate_and_job(
        profile_id=profile_id,
        job_id=request.job_id,
        job_title=request.job_title,
        current_user=current_user
    )

    result = application_agent.generate_cover_letter(
        candidate=candidate,
        job=job
    )

    now = datetime.now(timezone.utc).isoformat()
    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO cover_letters (profile_id, job_id, letter_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                profile_id,
                str(job.get("job_id", "")),
                json.dumps(result, ensure_ascii=False),
                now
            )
        )
        connection.commit()
    finally:
        connection.close()

    result["profile_id"] = profile_id
    result["job_id"] = job.get("job_id")
    return result


# ============================================================
# M3.3 — INTERVIEW PREPARATION
# ============================================================

@app.post("/profiles/{profile_id}/interview-prep")
def generate_interview_prep(
    profile_id: int,
    request: InterviewPrepInput,
    auth_request: Request
):
    current_user = get_optional_current_user(auth_request)
    candidate, job = resolve_candidate_and_job(
        profile_id=profile_id,
        job_id=request.job_id,
        job_title=request.job_title,
        current_user=current_user
    )

    # Check if recent skill gap exists for additional context
    skill_gap = None
    connection = get_connection()
    try:
        gap_row = connection.execute(
            """
            SELECT result_json
            FROM skill_gaps
            WHERE profile_id = ? AND job_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (profile_id, str(job.get("job_id", "")))
        ).fetchone()

        if gap_row:
            try:
                skill_gap = json.loads(gap_row["result_json"])
            except Exception:
                pass
    finally:
        connection.close()

    result = interview_agent.generate_interview_prep(
        candidate=candidate,
        job=job,
        skill_gap=skill_gap
    )

    now = datetime.now(timezone.utc).isoformat()
    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO interview_preps (profile_id, job_id, prep_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                profile_id,
                str(job.get("job_id", "")),
                json.dumps(result, ensure_ascii=False),
                now
            )
        )
        connection.commit()
    finally:
        connection.close()

    result["profile_id"] = profile_id
    result["job_id"] = job.get("job_id")
    return result


# ============================================================
# M3.3 — MOCK INTERVIEW SIMULATOR
# ============================================================

@app.post("/profiles/{profile_id}/mock-interview/start")
def start_mock_interview(
    profile_id: int,
    request: MockInterviewStartInput,
    auth_request: Request
):
    current_user = get_optional_current_user(auth_request)
    candidate, job = resolve_candidate_and_job(
        profile_id=profile_id,
        job_id=request.job_id,
        job_title=request.job_title,
        current_user=current_user
    )

    # Generate complete question bank
    prep_data = interview_agent.generate_interview_prep(
        candidate=candidate,
        job=job
    )

    # Select 5 curated sequential questions across categories
    curated_questions = []
    
    if prep_data.get("technical_questions"):
        curated_questions.append(prep_data["technical_questions"][0])
    if prep_data.get("project_questions"):
        curated_questions.append(prep_data["project_questions"][0])
    if len(prep_data.get("technical_questions", [])) > 1:
        curated_questions.append(prep_data["technical_questions"][1])
    if prep_data.get("resume_questions"):
        curated_questions.append(prep_data["resume_questions"][0])
    if prep_data.get("hr_questions"):
        curated_questions.append(prep_data["hr_questions"][0])

    if not curated_questions:
        curated_questions = [
            {
                "id": "q1",
                "category": "Technical",
                "question": f"Explain your core experience with {', '.join(job.get('required_skills', ['Python'])[:3])}.",
                "preparation_guide": "Walk through fundamental principles and practical applications.",
                "suggested_topics": ["Architecture", "Key libraries", "Testing"],
                "sample_answer_framework": "Definition -> Example -> Impact."
            }
        ]

    now = datetime.now(timezone.utc).isoformat()
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            INSERT INTO mock_interviews
            (profile_id, job_id, job_title, company, status, questions_json, current_index, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                str(job.get("job_id", "")),
                str(job.get("job_title", "Target Role")),
                str(job.get("company", "Target Company")),
                "in_progress",
                json.dumps(curated_questions, ensure_ascii=False),
                0,
                now
            )
        )
        connection.commit()
        interview_id = cursor.lastrowid
    finally:
        connection.close()

    return {
        "interview_id": interview_id,
        "profile_id": profile_id,
        "job_id": job.get("job_id"),
        "job_title": job.get("job_title"),
        "company": job.get("company"),
        "total_questions": len(curated_questions),
        "current_question_index": 0,
        "current_question": curated_questions[0],
        "status": "in_progress"
    }


@app.post("/profiles/{profile_id}/mock-interview/answer")
def submit_mock_interview_answer(
    profile_id: int,
    request: MockInterviewAnswerInput,
    auth_request: Request
):
    current_user = get_optional_current_user(auth_request)
    if current_user is not None:
        assert_profile_access(profile_id, current_user)
    connection = get_connection()
    session = connection.execute(
        """
        SELECT *
        FROM mock_interviews
        WHERE id = ? AND profile_id = ?
        """,
        (request.interview_id, profile_id)
    ).fetchone()

    if not session:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="Mock interview session not found."
        )

    questions = json.loads(session["questions_json"])
    candidate_row = connection.execute(
        "SELECT * FROM profiles WHERE id = ?", (profile_id,)
    ).fetchone()
    resume_row = connection.execute(
        "SELECT * FROM resumes WHERE profile_id = ? ORDER BY id DESC LIMIT 1", (profile_id,)
    ).fetchone()
    
    candidate = dict(candidate_row)
    if resume_row and resume_row["extraction_json"]:
        try:
            candidate.update(json.loads(resume_row["extraction_json"]))
        except Exception:
            pass

    job = {
        "job_id": session["job_id"],
        "job_title": session["job_title"],
        "company": session["company"]
    }

    # Evaluate answer
    evaluation = interview_agent.evaluate_mock_answer(
        candidate=candidate,
        job=job,
        question=request.question_text,
        answer=request.user_answer,
        category=request.category
    )

    now = datetime.now(timezone.utc).isoformat()

    # Record answer
    connection.execute(
        """
        INSERT INTO mock_interview_answers
        (interview_id, question_index, question_text, category, user_answer, evaluation_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request.interview_id,
            request.question_index,
            request.question_text,
            request.category,
            request.user_answer,
            json.dumps(evaluation, ensure_ascii=False),
            now
        )
    )

    next_index = request.question_index + 1
    is_completed = next_index >= len(questions)
    new_status = "completed" if is_completed else "in_progress"

    connection.execute(
        """
        UPDATE mock_interviews
        SET current_index = ?, status = ?
        WHERE id = ?
        """,
        (next_index, new_status, request.interview_id)
    )
    connection.commit()
    connection.close()

    next_question = questions[next_index] if not is_completed else None

    return {
        "interview_id": request.interview_id,
        "question_index": request.question_index,
        "evaluation": evaluation,
        "is_completed": is_completed,
        "next_question_index": next_index if not is_completed else None,
        "next_question": next_question,
        "total_questions": len(questions)
    }


@app.get("/profiles/{profile_id}/mock-interview/{interview_id}")
def get_mock_interview_details(
    profile_id: int,
    interview_id: int,
    request: Request
):
    current_user = get_optional_current_user(request)
    if current_user is not None:
        assert_profile_access(profile_id, current_user)
    connection = get_connection()
    session = connection.execute(
        """
        SELECT *
        FROM mock_interviews
        WHERE id = ? AND profile_id = ?
        """,
        (interview_id, profile_id)
    ).fetchone()

    if not session:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="Mock interview session not found."
        )

    answers = connection.execute(
        """
        SELECT *
        FROM mock_interview_answers
        WHERE interview_id = ?
        ORDER BY question_index ASC
        """,
        (interview_id,)
    ).fetchall()

    connection.close()

    parsed_answers = []
    for a in answers:
        item = dict(a)
        if item.get("evaluation_json"):
            try:
                item["evaluation"] = json.loads(item["evaluation_json"])
            except Exception:
                item["evaluation"] = {}
        parsed_answers.append(item)

    session_dict = dict(session)
    session_dict["questions"] = json.loads(session_dict.get("questions_json", "[]"))
    session_dict["answers"] = parsed_answers
    return session_dict


# ============================================================
# M4.1 — APPLICATION TRACKING & MANAGEMENT APIS
# ============================================================

def format_application_row(row, connection=None):
    if not row:
        return None
    app_dict = dict(row)

    for key in ["customized_resume", "cover_letter"]:
        val = app_dict.get(key)
        if val and isinstance(val, str):
            try:
                app_dict[key] = json.loads(val)
            except Exception:
                pass

    if connection and app_dict.get("job_id") and app_dict.get("profile_id"):
        if not app_dict.get("customized_resume"):
            cr_row = connection.execute(
                "SELECT resume_json FROM customized_resumes WHERE profile_id = ? AND job_id = ? ORDER BY id DESC LIMIT 1",
                (app_dict["profile_id"], str(app_dict["job_id"]))
            ).fetchone()
            if cr_row and cr_row["resume_json"]:
                try:
                    app_dict["customized_resume"] = json.loads(cr_row["resume_json"])
                except Exception:
                    app_dict["customized_resume"] = cr_row["resume_json"]

        if not app_dict.get("cover_letter"):
            cl_row = connection.execute(
                "SELECT letter_json FROM cover_letters WHERE profile_id = ? AND job_id = ? ORDER BY id DESC LIMIT 1",
                (app_dict["profile_id"], str(app_dict["job_id"]))
            ).fetchone()
            if cl_row and cl_row["letter_json"]:
                try:
                    app_dict["cover_letter"] = json.loads(cl_row["letter_json"])
                except Exception:
                    app_dict["cover_letter"] = cl_row["letter_json"]

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    deadline_status = "none"
    if app_dict.get("deadline"):
        d_str = str(app_dict["deadline"])[:10]
        if d_str < today_str:
            deadline_status = "overdue"
        elif d_str == today_str:
            deadline_status = "due_today"
        else:
            deadline_status = "upcoming"
    app_dict["deadline_status"] = deadline_status
    return app_dict


@app.post("/profiles/{profile_id}/applications")
def create_application(
    profile_id: int,
    request: ApplicationCreateInput,
    auth_request: Request
):
    current_user = get_optional_current_user(auth_request)
    if current_user is not None:
        assert_profile_access(profile_id, current_user)

    connection = get_connection()
    try:
        profile = connection.execute(
            "SELECT id FROM profiles WHERE id = ?", (profile_id,)
        ).fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found.")

        if request.status and request.status not in VALID_APPLICATION_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{request.status}'. Allowed: {', '.join(VALID_APPLICATION_STATUSES)}"
            )

        if request.job_id:
            existing = connection.execute(
                "SELECT id FROM applications WHERE profile_id = ? AND job_id = ?",
                (profile_id, str(request.job_id))
            ).fetchone()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"An application for job ID '{request.job_id}' already exists for this profile."
                )

        now = datetime.now(timezone.utc).isoformat()
        app_date = request.application_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        cust_resume_str = json.dumps(request.customized_resume) if isinstance(request.customized_resume, (dict, list)) else request.customized_resume
        cover_letter_str = json.dumps(request.cover_letter) if isinstance(request.cover_letter, (dict, list)) else request.cover_letter

        cursor = connection.execute(
            """
            INSERT INTO applications (
                profile_id, job_id, company_name, job_title, job_description,
                application_date, deadline, status, interview_date, interview_status,
                notes, follow_up_date, customized_resume, cover_letter, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                str(request.job_id) if request.job_id else None,
                request.company_name.strip(),
                request.job_title.strip(),
                request.job_description,
                app_date,
                request.deadline,
                request.status,
                request.interview_date,
                request.interview_status,
                request.notes,
                request.follow_up_date,
                cust_resume_str,
                cover_letter_str,
                now,
                now,
            )
        )
        connection.commit()
        app_id = cursor.lastrowid
        row = connection.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
        return format_application_row(row, connection)
    finally:
        connection.close()


@app.get("/profiles/{profile_id}/applications")
def get_applications(
    profile_id: int,
    auth_request: Request,
    search: str | None = None,
    company: str | None = None,
    role: str | None = None,
    status: str | None = None,
    deadline_filter: str | None = None,
    application_date: str | None = None
):
    current_user = get_optional_current_user(auth_request)
    if current_user is not None:
        assert_profile_access(profile_id, current_user)

    connection = get_connection()
    try:
        profile = connection.execute(
            "SELECT id FROM profiles WHERE id = ?", (profile_id,)
        ).fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found.")

        query = "SELECT * FROM applications WHERE profile_id = ?"
        params = [profile_id]

        if company:
            query += " AND LOWER(company_name) LIKE ?"
            params.append(f"%{company.lower().strip()}%")

        if role:
            query += " AND LOWER(job_title) LIKE ?"
            params.append(f"%{role.lower().strip()}%")

        if status:
            query += " AND status = ?"
            params.append(status.strip())

        if application_date:
            query += " AND application_date LIKE ?"
            params.append(f"{application_date}%")

        if search:
            s = f"%{search.lower().strip()}%"
            query += " AND (LOWER(company_name) LIKE ? OR LOWER(job_title) LIKE ? OR LOWER(COALESCE(job_description, '')) LIKE ? OR LOWER(COALESCE(notes, '')) LIKE ?)"
            params.extend([s, s, s, s])

        query += " ORDER BY updated_at DESC, id DESC"

        rows = connection.execute(query, params).fetchall()
        results = [format_application_row(r, connection) for r in rows]

        if deadline_filter:
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if deadline_filter == "upcoming":
                results = [r for r in results if r.get("deadline") and str(r["deadline"])[:10] >= today_str]
            elif deadline_filter == "overdue":
                results = [r for r in results if r.get("deadline") and str(r["deadline"])[:10] < today_str and r.get("status") not in ["Rejected", "Withdrawn", "Offer received"]]
            elif deadline_filter == "has_deadline":
                results = [r for r in results if r.get("deadline")]

        return {"profile_id": profile_id, "count": len(results), "applications": results}
    finally:
        connection.close()


@app.get("/profiles/{profile_id}/applications/dashboard")
def get_application_dashboard(
    profile_id: int,
    auth_request: Request
):
    current_user = get_optional_current_user(auth_request)
    if current_user is not None:
        assert_profile_access(profile_id, current_user)

    connection = get_connection()
    try:
        profile = connection.execute(
            "SELECT id FROM profiles WHERE id = ?", (profile_id,)
        ).fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found.")

        rows = connection.execute(
            "SELECT * FROM applications WHERE profile_id = ? ORDER BY updated_at DESC",
            (profile_id,)
        ).fetchall()
        apps = [format_application_row(r, connection) for r in rows]

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        total_applications = len(apps)
        active_applications = sum(1 for a in apps if a["status"] not in ["Rejected", "Withdrawn"])
        offers_received = sum(1 for a in apps if a["status"] == "Offer received")
        rejected_applications = sum(1 for a in apps if a["status"] == "Rejected")

        upcoming_deadlines_count = sum(
            1 for a in apps
            if a.get("deadline") and str(a["deadline"])[:10] >= today_str and a["status"] not in ["Rejected", "Withdrawn", "Offer received"]
        )

        interviews_scheduled_count = sum(
            1 for a in apps
            if a["status"] == "Interview scheduled" or (a.get("interview_date") and str(a["interview_date"])[:10] >= today_str and a["status"] not in ["Rejected", "Withdrawn"])
        )

        upcoming_deadlines_list = [
            a for a in apps
            if a.get("deadline") and str(a["deadline"])[:10] >= today_str and a["status"] not in ["Rejected", "Withdrawn", "Offer received"]
        ]
        upcoming_deadlines_list.sort(key=lambda x: str(x.get("deadline")))

        recent_applications_list = sorted(apps, key=lambda x: str(x.get("created_at")), reverse=True)[:5]

        upcoming_interviews_list = [
            a for a in apps
            if a.get("interview_date") and str(a["interview_date"])[:10] >= today_str and a["status"] not in ["Rejected", "Withdrawn"]
        ]
        upcoming_interviews_list.sort(key=lambda x: str(x.get("interview_date")))

        needing_followup_list = [
            a for a in apps
            if a.get("follow_up_date") and a["status"] not in ["Rejected", "Withdrawn", "Offer received"]
        ]
        needing_followup_list.sort(key=lambda x: str(x.get("follow_up_date")))

        return {
            "profile_id": profile_id,
            "metrics": {
                "total_applications": total_applications,
                "active_applications": active_applications,
                "upcoming_deadlines": upcoming_deadlines_count,
                "interviews_scheduled": interviews_scheduled_count,
                "offers_received": offers_received,
                "rejected_applications": rejected_applications,
            },
            "lists": {
                "upcoming_deadlines": upcoming_deadlines_list[:5],
                "recent_applications": recent_applications_list,
                "upcoming_interviews": upcoming_interviews_list[:5],
                "needing_followup": needing_followup_list[:5],
            }
        }
    finally:
        connection.close()


@app.get("/profiles/{profile_id}/applications/{application_id}")
def get_application_by_id(
    profile_id: int,
    application_id: int,
    auth_request: Request
):
    current_user = get_optional_current_user(auth_request)
    if current_user is not None:
        assert_profile_access(profile_id, current_user)

    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM applications WHERE id = ? AND profile_id = ?",
            (application_id, profile_id)
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Application not found.")

        return format_application_row(row, connection)
    finally:
        connection.close()


@app.put("/profiles/{profile_id}/applications/{application_id}")
def update_application(
    profile_id: int,
    application_id: int,
    request: ApplicationUpdateInput,
    auth_request: Request
):
    current_user = get_optional_current_user(auth_request)
    if current_user is not None:
        assert_profile_access(profile_id, current_user)

    connection = get_connection()
    try:
        existing = connection.execute(
            "SELECT * FROM applications WHERE id = ? AND profile_id = ?",
            (application_id, profile_id)
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Application not found.")

        if request.status and request.status not in VALID_APPLICATION_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{request.status}'. Allowed: {', '.join(VALID_APPLICATION_STATUSES)}"
            )

        update_data = request.model_dump(exclude_unset=True)
        if not update_data:
            return format_application_row(existing, connection)

        set_clauses = []
        params = []
        for key, value in update_data.items():
            if key in ["customized_resume", "cover_letter"] and isinstance(value, (dict, list)):
                value = json.dumps(value)
            set_clauses.append(f"{key} = ?")
            params.append(value)

        now = datetime.now(timezone.utc).isoformat()
        set_clauses.append("updated_at = ?")
        params.append(now)

        params.extend([application_id, profile_id])
        query = f"UPDATE applications SET {', '.join(set_clauses)} WHERE id = ? AND profile_id = ?"
        connection.execute(query, params)
        connection.commit()

        updated_row = connection.execute(
            "SELECT * FROM applications WHERE id = ? AND profile_id = ?",
            (application_id, profile_id)
        ).fetchone()
        return format_application_row(updated_row, connection)
    finally:
        connection.close()


@app.delete("/profiles/{profile_id}/applications/{application_id}")
def delete_application(
    profile_id: int,
    application_id: int,
    auth_request: Request
):
    current_user = get_optional_current_user(auth_request)
    if current_user is not None:
        assert_profile_access(profile_id, current_user)

    connection = get_connection()
    try:
        existing = connection.execute(
            "SELECT * FROM applications WHERE id = ? AND profile_id = ?",
            (application_id, profile_id)
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Application not found.")

        connection.execute(
            "DELETE FROM applications WHERE id = ? AND profile_id = ?",
            (application_id, profile_id)
        )
        connection.commit()
        return {"message": "Application deleted successfully", "application_id": application_id}
    finally:
        connection.close()


# ============================================================
# M3.4 — CONVERSATIONAL CAREER ASSISTANT
# ============================================================

@app.post("/career-assistant/chat")
def chat_career_assistant(request: CareerAssistantInput, auth_request: Request):
    current_user = get_optional_current_user(auth_request)
    if request.profile_id and current_user is not None:
        assert_profile_access(request.profile_id, current_user)

    profile = {}
    job = {}
    skill_gap = {}
    conversation_id = request.conversation_id or (
        f"profile_{request.profile_id}_default" if request.profile_id else "default_conversation"
    )

    connection = get_connection()

    if request.profile_id:
        profile_row = connection.execute(
            "SELECT * FROM profiles WHERE id = ?", (request.profile_id,)
        ).fetchone()

        if profile_row:
            profile = dict(profile_row)
            resume_row = connection.execute(
                "SELECT * FROM resumes WHERE profile_id = ? ORDER BY id DESC LIMIT 1",
                (request.profile_id,)
            ).fetchone()

            if resume_row and resume_row["extraction_json"]:
                try:
                    profile.update(json.loads(resume_row["extraction_json"]))
                except Exception:
                    pass

            if request.job_id:
                gap_row = connection.execute(
                    "SELECT result_json FROM skill_gaps WHERE profile_id = ? AND job_id = ? ORDER BY id DESC LIMIT 1",
                    (request.profile_id, str(request.job_id))
                ).fetchone()
                if gap_row:
                    try:
                        skill_gap = json.loads(gap_row["result_json"])
                    except Exception:
                        pass

    if request.job_id:
        all_jobs = get_cached_jobs()
        job = JOB_CACHE_BY_ID.get(str(request.job_id), {})
        if not job:
            for j in all_jobs:
                if str(j.get("job_id")) == str(request.job_id):
                    job = j
                    break

    # Run conversational assistant turn
    response = career_assistant.chat(
        message=request.message,
        profile=profile,
        job=job,
        skill_gap=skill_gap,
        history=request.history
    )
    response["conversation_id"] = conversation_id

    # Persist chat message if profile_id is provided
    if request.profile_id:
        now = datetime.now(timezone.utc).isoformat()
        try:
            # User message
            connection.execute(
                """
                INSERT INTO chat_messages (profile_id, job_id, conversation_id, role, content, context_used_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (request.profile_id, request.job_id, conversation_id, "user", request.message, None, now)
            )
            # Assistant response
            connection.execute(
                """
                INSERT INTO chat_messages (profile_id, job_id, conversation_id, role, content, context_used_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.profile_id,
                    request.job_id,
                    conversation_id,
                    "assistant",
                    response.get("message", ""),
                    json.dumps(response.get("context_used", {})),
                    now
                )
            )
            connection.commit()
        except Exception:
            pass

    connection.close()
    return response


@app.get("/career-assistant/history/{profile_id}")
def get_chat_history(profile_id: int, request: Request, conversation_id: str | None = None):
    current_user = get_optional_current_user(request)
    if current_user is not None:
        assert_profile_access(profile_id, current_user)
    connection = get_connection()
    if conversation_id:
        messages = connection.execute(
            """
            SELECT role, content, created_at, job_id, conversation_id
            FROM chat_messages
            WHERE profile_id = ? AND conversation_id = ?
            ORDER BY id ASC
            LIMIT 50
            """,
            (profile_id, conversation_id)
        ).fetchall()
    else:
        messages = connection.execute(
            """
            SELECT role, content, created_at, job_id, conversation_id
            FROM chat_messages
            WHERE profile_id = ?
            ORDER BY id ASC
            LIMIT 50
            """,
            (profile_id,)
        ).fetchall()
    connection.close()

    return {
        "profile_id": profile_id,
        "conversation_id": conversation_id,
        "messages": [dict(m) for m in messages]
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name": "AI Career Companion Agent",
        "version": "0.6.0",
        "status": "running",
        "docs": "/docs",
        "milestones": ["M1", "M2", "M3"]
    }