import json
import time
import os
import re
import shutil
import sqlite3
import sys

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
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
# RAG + MATCHING IMPORTS
# ============================================================

from backend.rag.retriever import JobRetriever
from backend.matching.service import MatchingService


# ============================================================
# PATH CONFIGURATION
# ============================================================

DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DATABASE = DATA_DIR / "career_companion.db"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)


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
    version="0.3.0"
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


# ============================================================
# PROFILE MODEL
# ============================================================

class ProfileInput(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    location: str | None = None
    target_role: str | None = None
    linkedin_url: str | None = None


# ============================================================
# JOB SEARCH MODEL
# ============================================================

class JobSearchInput(BaseModel):
    query: str
    top_k: int = 5


# ============================================================
# JOB MATCH MODEL
# ============================================================

class JobMatchInput(BaseModel):
    top_k: int = 5


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def create_database():

    connection = get_connection()

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            location TEXT,
            target_role TEXT,
            linkedin_url TEXT,
            created_at TEXT NOT NULL
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
        """
    )

    connection.commit()
    connection.close()


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

        matching_service = MatchingService()

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
def create_profile(
    profile: ProfileInput
):

    connection = get_connection()

    existing = connection.execute(
        """
        SELECT *
        FROM profiles
        WHERE email = ?
        """,
        (
            str(profile.email),
        )
    ).fetchone()

    if existing:

        connection.close()

        return dict(existing)

    now = datetime.now(
        timezone.utc
    ).isoformat()

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
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            profile.full_name,
            str(profile.email),
            profile.phone,
            profile.location,
            profile.target_role,
            profile.linkedin_url,
            now
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

    connection.close()

    return dict(saved_profile)


# ============================================================
# RESUME TEXT EXTRACTION
# ============================================================

def extract_text(file_path: Path):

    suffix = file_path.suffix.lower()

    # --------------------------------------------------------
    # TXT
    # --------------------------------