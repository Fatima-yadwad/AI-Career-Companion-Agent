import json
import os
import re
import shutil
import sqlite3
import sys
import time
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
    version="0.4.0"
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
        r"(B\.?Tech.{0,120})",
        r"(Bachelor.{0,120})",
        r"(M\.?Tech.{0,120})",
        r"(Master.{0,120})",
        r"(B\.?Sc.{0,120})",
        r"(M\.?Sc.{0,120})",
        r"(Ph\.?D.{0,120})"
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
        flags=re.IGNORECASE
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
        flags=re.IGNORECASE
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

    # Remove ```json ... ``` if returned
    raw_text = re.sub(
        r"^```json\s*",
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

    IMPORTANT:
    Gemini does NOT calculate the match score.

    The matching service already calculates:
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
    #
    # Deliberately remove existing "reasoning" because
    # that reasoning may have been generated by the
    # deterministic matching service.
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

            # Keep useful evidence only
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

        # Internal index guarantees that even if job_id
        # is missing, we can still map the explanation.
        evidence["_result_index"] = index

        job_evidence.append(
            evidence
        )

    prompt = f"""
You are an AI career advisor.

Your task is to explain why each recommended job
is a good or moderate match for the candidate.

IMPORTANT:

1. Do NOT calculate or modify the match score.
2. Do NOT invent candidate skills.
3. Do NOT invent job requirements.
4. Use ONLY the candidate information and matching
   evidence supplied below.
5. Mention strong skill alignment when appropriate.
6. Mention relevant projects or education when the
   supplied evidence supports it.
7. Mention important missing skills when present.
8. Be honest about weaknesses.
9. Do not say the candidate is "perfect" unless the
   evidence genuinely supports that.
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

            key = (
                str(job_id)
                if job_id is not None
                else str(result_index)
            )

            explanations[key] = reasoning

    return explanations


# ============================================================
# RESUME UPLOAD + ANALYSIS
# ============================================================

@app.post("/profiles/{profile_id}/resumes")
async def upload_resume(
    profile_id: int,
    file: UploadFile = File(...)
):

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
        file.filename
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

        # IMPORTANT:
        # Frontend checks for "gemini_llm"
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
def get_latest_resume(
    profile_id: int
):

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
def search_jobs(
    request: JobSearchInput
):

    if job_retriever is None:

        raise HTTPException(
            status_code=503,
            detail="RAG job retriever is unavailable."
        )

    results = job_retriever.search(
        request.query,
        top_k=request.top_k
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
    request: JobMatchInput
):

    if matching_service is None:

        raise HTTPException(
            status_code=503,
            detail="Matching service is unavailable."
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
    #
    # This part remains unchanged.
    # The matching service calculates:
    # - match score
    # - matched skills
    # - missing skills
    # - qualification scores
    # - retrieval similarity
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

        # We DO NOT generate a hard-coded explanation.
        # Instead, clearly indicate that the AI explanation
        # could not be generated.
        explanations = {}

        explanation_source = "unavailable"

    # --------------------------------------------------------
    # Attach Gemini explanations
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

        # If job_id was not available, try result index
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
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "name": "AI Career Companion Agent",
        "version": "0.4.0",
        "status": "running",
        "docs": "/docs"
    }