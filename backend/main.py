import json
import time
import os
import re
import shutil
import sqlite3

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

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
    version="0.1.0"
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

@app.on_event("startup")
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
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "ok"
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

        from pypdf import PdfReader

        reader = PdfReader(file_path)

        text = []

        for page in reader.pages:

            page_text = page.extract_text() or ""

            text.append(page_text)

        return "\n".join(text)


    # --------------------------------------------------------
    # DOCX
    # --------------------------------------------------------

    if suffix == ".docx":

        from docx import Document

        document = Document(file_path)

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )


    raise HTTPException(
        status_code=400,
        detail=(
            "Only PDF, DOCX, and TXT files are supported."
        )
    )


# ============================================================
# LOCAL FALLBACK EXTRACTION
# ============================================================

def local_fallback_extraction(text: str):

    """
    Local rule-based resume extraction.

    Used when Gemini is unavailable or fails.
    """

    # ========================================================
    # CLEAN TEXT
    # ========================================================

    text = text.replace(
        "\r",
        "\n"
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]


    # ========================================================
    # KNOWN SKILLS
    # ========================================================

    known_skills = [

        "Python",
        "Java",
        "C++",
        "C",
        "JavaScript",
        "TypeScript",

        "HTML",
        "CSS",
        "React",
        "Node.js",
        "FastAPI",
        "Flask",
        "Django",

        "SQL",
        "MySQL",
        "PostgreSQL",
        "MongoDB",
        "SQLite",
        "NoSQL",

        "Git",
        "GitHub",
        "Docker",
        "REST API",
        "API",

        "AWS",
        "Azure",
        "Google Cloud",
        "GCP",

        "Artificial Intelligence",
        "Machine Learning",
        "Deep Learning",
        "Generative AI",
        "GenAI",

        "TensorFlow",
        "PyTorch",
        "Scikit-learn",
        "OpenCV",

        "Pandas",
        "NumPy",
        "Data Science",
        "Data Analytics",

        "Power BI",
        "Tableau",
        "Matplotlib",

        "R",
        "Kubernetes",
        "Figma",
        "DBMS",
        "OOP",
        "DSA",
        "Operating Systems",
        "Computer Networks"
    ]


    skills = []

    for skill in known_skills:

        pattern = (
            rf"(?<!\w)"
            rf"{re.escape(skill)}"
            rf"(?!\w)"
        )

        if re.search(
            pattern,
            text,
            re.IGNORECASE
        ):

            skills.append(skill)


    # ========================================================
    # SECTION DETECTION
    # ========================================================

    section_aliases = {

        "education": [
            "education",
            "academic background",
            "academic qualifications",
            "educational background"
        ],

        "experience": [
            "experience",
            "work experience",
            "professional experience",
            "internship experience",
            "work history"
        ],

        "projects": [
            "projects",
            "academic projects",
            "personal projects",
            "project experience"
        ],

        "certifications": [
            "certifications",
            "certificates",
            "courses",
            "achievements"
        ],

        "skills": [
            "skills",
            "technical skills",
            "technical expertise",
            "technical skills & tools"
        ]
    }


    sections = {

        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
        "skills": []
    }


    current_section = None


    for line in lines:

        normalized = re.sub(
            r"[^a-zA-Z &]",
            "",
            line
        ).strip().lower()

        detected_section = None


        for section, aliases in section_aliases.items():

            for alias in aliases:

                if normalized == alias:

                    detected_section = section

                    break

            if detected_section:
                break


        if detected_section:

            current_section = detected_section

            continue


        if current_section:

            sections[current_section].append(line)


    # ========================================================
    # EDUCATION EXTRACTION
    # ========================================================

    education = []

    education_lines = sections["education"]


    degree_keywords = [

        "B.E",
        "B.Tech",
        "Bachelor",
        "M.Tech",
        "M.E",
        "Master",
        "MBA",
        "BCA",
        "MCA",
        "B.Sc",
        "M.Sc",
        "PUC",
        "12th",
        "10th",
        "SSLC",
        "Diploma"
    ]


    year_pattern = re.compile(
        r"\b(?:19|20)\d{2}"
        r"(?:\s*[-–]\s*(?:19|20)\d{2})?\b"
    )


    used_education = set()


    for index, line in enumerate(
        education_lines
    ):

        if not any(
            keyword.lower() in line.lower()
            for keyword in degree_keywords
        ):
            continue


        year_match = year_pattern.search(line)

        year = (
            year_match.group(0)
            if year_match
            else ""
        )


        degree = line

        if year:

            degree = degree.replace(
                year,
                ""
            ).strip()


        institution = ""


        nearby_start = max(
            0,
            index - 2
        )


        nearby_lines = education_lines[
            nearby_start:index
        ]


        for previous_line in reversed(
            nearby_lines
        ):

            lower = previous_line.lower()

            if not any(
                keyword.lower() in lower
                for keyword in degree_keywords
            ):

                institution = previous_line

                break


        key = (
            institution.lower(),
            degree.lower(),
            year
        )


        if key in used_education:
            continue


        used_education.add(key)


        education.append(
            {
                "institution": institution,
                "degree": degree,
                "year": year
            }
        )


    # ========================================================
    # EXPERIENCE EXTRACTION
    # ========================================================

    experience = []

    experience_lines = sections["experience"]


    duration_pattern = re.compile(
        r"(?i)"
        r"(?:"
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        r"[a-z]*\s+\d{4}"
        r"\s*[-–]\s*"
        r"(?:"
        r"Present"
        r"|"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        r"[a-z]*\s+\d{4}"
        r")"
        r")"
        r"|"
        r"\b\d{4}\s*[-–]\s*(?:\d{4}|Present)\b"
    )


    current_experience = None


    for line in experience_lines:

        duration_match = duration_pattern.search(
            line
        )


        if duration_match:

            if current_experience:

                experience.append(
                    current_experience
                )


            duration = duration_match.group(0)


            role = line.replace(
                duration,
                ""
            ).strip()


            current_experience = {

                "company": "",

                "role": role,

                "duration": duration,

                "highlights": []
            }


            continue


        if line.startswith(
            ("•", "-", "*")
        ):

            if current_experience:

                current_experience[
                    "highlights"
                ].append(
                    line.lstrip(
                        "•-* "
                    ).strip()
                )

            continue


        if current_experience:

            if not current_experience["company"]:

                current_experience[
                    "company"
                ] = line


    if current_experience:

        experience.append(
            current_experience
        )


    experience = experience[:10]


    # ========================================================
    # PROJECT EXTRACTION
    # ========================================================

    projects = []

    project_lines = sections["projects"]

    current_project = None


    for line in project_lines:

        if not line.strip():
            continue


        if line.startswith(
            ("•", "-", "*")
        ):

            if current_project:

                description = line.lstrip(
                    "•-* "
                ).strip()

                current_project[
                    "description"
                ] += " " + description

            continue


        lower_line = line.lower()


        description_words = [

            "built a",
            "developed a",
            "implemented",
            "designed a",
            "performed",
            "improved",
            "created a",
            "developed",
            "built"
        ]


        is_description = any(
            word in lower_line
            for word in description_words
        )


        if not is_description:

            if current_project:

                projects.append(
                    current_project
                )


            technologies = []


            for skill in skills:

                pattern = (
                    rf"(?<!\w)"
                    rf"{re.escape(skill)}"
                    rf"(?!\w)"
                )


                if re.search(
                    pattern,
                    line,
                    re.IGNORECASE
                ):

                    technologies.append(
                        skill
                    )


            project_name = re.split(
                r"\s*\|\s*",
                line
            )[0].strip()


            current_project = {

                "name": project_name,

                "description": "",

                "technologies": technologies
            }


        else:

            if current_project:

                current_project[
                    "description"
                ] += " " + line


    if current_project:

        projects.append(
            current_project
        )


    projects = projects[:10]


    # ========================================================
    # CERTIFICATIONS
    # ========================================================

    certifications = []

    certification_lines = sections[
        "certifications"
    ]


    for line in certification_lines:

        cleaned = line.lstrip(
            "•-* "
        ).strip()


        if cleaned:

            certifications.append(
                cleaned
            )


    certifications = list(
        dict.fromkeys(
            certifications
        )
    )[:10]


    # ========================================================
    # SUMMARY
    # ========================================================

    summary = (
        "Resume processed using local "
        "structured extraction because "
        "the Gemini service was unavailable."
    )


    # ========================================================
    # RETURN
    # ========================================================

    return {

        "summary": summary,

        "skills": skills,

        "education": education,

        "experience": experience,

        "projects": projects,

        "certifications": certifications
    }


# ============================================================
# GEMINI + FALLBACK EXTRACTION
# ============================================================

def extract_resume_data(text: str):

    """
    Resume extraction pipeline.

    Priority:
    1. Gemini 3.6 Flash
    2. Local rule-based fallback
    """

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )


    if not api_key:

        print(
            "GEMINI_API_KEY not found."
        )

        print(
            "Using local resume extraction."
        )

        return (
            local_fallback_extraction(text),
            "local_fallback"
        )


    try:

        from google import genai


        client = genai.Client(
            api_key=api_key
        )


        model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.6-flash"
        )


        # Keep enough resume text for parsing
        resume_text = text[:8000]


        prompt = f"""
You are an expert resume parsing system.

Analyze the resume text below and extract structured information.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "summary": "short professional summary",
    "skills": [],
    "education": [
        {{
            "institution": "",
            "degree": "",
            "year": ""
        }}
    ],
    "experience": [
        {{
            "company": "",
            "role": "",
            "duration": "",
            "highlights": []
        }}
    ],
    "projects": [
        {{
            "name": "",
            "description": "",
            "technologies": []
        }}
    ],
    "certifications": []
}}

Rules:

1. Extract ONLY information present in the resume.
2. Do NOT invent information.
3. Correct obvious PDF extraction spacing errors.
4. Preserve institution names.
5. Preserve project names.
6. Keep education, experience, projects and certifications separate.
7. Put technical abilities in skills.
8. If a section is missing, return an empty array.
9. Return JSON only.

Resume text:

{resume_text}
"""


        print(
            "\n========== GEMINI REQUEST =========="
        )

        print(
            f"Model: {model}"
        )

        print(
            f"Characters sent: {len(resume_text)}"
        )


        start_time = time.time()


        response = client.models.generate_content(
            model=model,
            contents=prompt
        )


        elapsed = time.time() - start_time


        print(
            f"Gemini response received in "
            f"{elapsed:.2f} seconds."
        )


        content = response.text


        if not content:

            raise ValueError(
                "Gemini returned an empty response."
            )


        print(
            "Gemini raw response received."
        )


        # ====================================================
        # CLEAN RESPONSE
        # ====================================================

        content = content.strip()


        if content.startswith("```"):

            content = re.sub(
                r"^```(?:json)?\s*",
                "",
                content,
                flags=re.IGNORECASE
            )

            content = re.sub(
                r"\s*```$",
                "",
                content
            ).strip()


        # ====================================================
        # PARSE JSON
        # ====================================================

        data = json.loads(content)


        # ====================================================
        # VALIDATE STRUCTURE
        # ====================================================

        required_fields = [

            "summary",
            "skills",
            "education",
            "experience",
            "projects",
            "certifications"
        ]


        for field in required_fields:

            if field not in data:

                raise ValueError(
                    f"Gemini response missing field: {field}"
                )


        # ====================================================
        # SUCCESS
        # ====================================================

        print(
            "Resume extracted successfully using Gemini."
        )


        return (
            data,
            "gemini_llm"
        )


    except Exception as error:

        print(
            f"Gemini extraction failed: {error}"
        )

        print(
            "Falling back to local resume extraction."
        )


        return (
            local_fallback_extraction(text),
            "local_fallback"
        )


# ============================================================
# RESUME UPLOAD
# ============================================================

@app.post(
    "/profiles/{profile_id}/resumes"
)
async def upload_resume(

    profile_id: int,

    file: UploadFile = File(...)
):

    connection = get_connection()


    # ========================================================
    # CHECK PROFILE
    # ========================================================

    profile = connection.execute(
        """
        SELECT id
        FROM profiles
        WHERE id = ?
        """,
        (
            profile_id,
        )
    ).fetchone()


    if not profile:

        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Profile not found."
        )


    # ========================================================
    # CHECK FILE
    # ========================================================

    if not file.filename:

        connection.close()

        raise HTTPException(
            status_code=400,
            detail="Filename is missing."
        )


    suffix = Path(
        file.filename
    ).suffix.lower()


    # ========================================================
    # CHECK FILE TYPE
    # ========================================================

    if suffix not in {
        ".pdf",
        ".docx",
        ".txt"
    }:

        connection.close()

        raise HTTPException(
            status_code=400,
            detail=(
                "Upload PDF, DOCX, or TXT only."
            )
        )


    # ========================================================
    # SAVE FILE
    # ========================================================

    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S"
    )


    saved_path = (
        UPLOAD_DIR
        / f"{profile_id}_{timestamp}{suffix}"
    )


    try:

        with saved_path.open("wb") as output_file:

            shutil.copyfileobj(
                file.file,
                output_file
            )


    except Exception as error:

        connection.close()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not save resume: {error}"
            )
        )


    # ========================================================
    # PARSE + EXTRACT
    # ========================================================

    try:

        resume_text = extract_text(
            saved_path
        )


        # ====================================================
        # DEBUG INFORMATION
        # ====================================================

        print(
            "\n========== RESUME TEXT =========="
        )

        print(
            resume_text[:3000]
        )

        print(
            "========== END RESUME TEXT ==========\n"
        )

        print(
            "========== EXTRACTED TEXT LENGTH =========="
        )

        print(
            len(resume_text)
        )

        print(
            "============================================"
        )


        if not resume_text.strip():

            raise ValueError(
                "No readable text was found "
                "in this resume."
            )


        # ====================================================
        # GEMINI / FALLBACK
        # ====================================================

        extracted_data, method = (
            extract_resume_data(
                resume_text
            )
        )


    except Exception as error:

        saved_path.unlink(
            missing_ok=True
        )

        connection.close()

        raise HTTPException(
            status_code=422,
            detail=(
                f"Could not parse resume: {error}"
            )
        )


    # ========================================================
    # SAVE TO DATABASE
    # ========================================================

    uploaded_at = datetime.now(
        timezone.utc
    ).isoformat()


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
                file.filename,
                str(saved_path),
                file.content_type,
                saved_path.stat().st_size,
                uploaded_at,
                json.dumps(
                    extracted_data
                ),
                method
            )
        )


        connection.commit()


    except Exception as error:

        connection.rollback()

        connection.close()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not save resume data: {error}"
            )
        )


    connection.close()


    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "resume_id": cursor.lastrowid,

        "filename": file.filename,

        "extraction_method": method,

        "extraction": extracted_data
    }