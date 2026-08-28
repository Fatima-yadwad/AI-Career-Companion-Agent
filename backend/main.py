import json
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


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
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
        (str(profile.email),)
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
        (cursor.lastrowid,)
    ).fetchone()

    connection.close()

    return dict(saved_profile)


# ============================================================
# RESUME TEXT EXTRACTION
# ============================================================

def extract_text(
    file_path: Path
):

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

        reader = PdfReader(
            file_path
        )

        text = []

        for page in reader.pages:

            text.append(
                page.extract_text() or ""
            )

        return "\n".join(text)


    # --------------------------------------------------------
    # DOCX
    # --------------------------------------------------------

    if suffix == ".docx":

        from docx import Document

        document = Document(
            file_path
        )

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )


    raise HTTPException(
        status_code=400,
        detail=(
            "Only PDF, DOCX, and TXT "
            "files are supported."
        )
    )


# ============================================================
# LOCAL FALLBACK EXTRACTION
# ============================================================

def local_fallback_extraction(
    text: str
):

    """
    Local rule-based resume extraction.

    This is used when:
    - OPENAI_API_KEY is missing
    - OpenAI quota is unavailable
    - OpenAI API returns an error
    - LLM response cannot be parsed
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

        # Programming
        "Python",
        "Java",
        "C++",
        "C",
        "JavaScript",
        "TypeScript",

        # Web
        "HTML",
        "CSS",
        "React",
        "Node.js",
        "FastAPI",
        "Flask",
        "Django",

        # Databases
        "SQL",
        "MySQL",
        "PostgreSQL",
        "MongoDB",
        "SQLite",
        "NoSQL",

        # Development
        "Git",
        "GitHub",
        "Docker",
        "REST API",
        "API",

        # Cloud
        "AWS",
        "Azure",
        "Google Cloud",
        "GCP",

        # AI / ML
        "Artificial Intelligence",
        "Machine Learning",
        "Deep Learning",
        "Generative AI",
        "GenAI",

        # ML libraries
        "TensorFlow",
        "PyTorch",
        "Scikit-learn",
        "OpenCV",

        # Data
        "Pandas",
        "NumPy",
        "Data Science",
        "Data Analytics",

        # Visualization
        "Power BI",
        "Tableau",
        "Matplotlib",

        # Other
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

            sections[
                current_section
            ].append(line)


    # ========================================================
    # EDUCATION EXTRACTION
    # ========================================================

    education = []

    education_lines = sections[
        "education"
    ]


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


        year_match = year_pattern.search(
            line
        )


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


        education.append({

            "institution": institution,

            "degree": degree,

            "year": year
        })


    # ========================================================
    # EXPERIENCE EXTRACTION
    # ========================================================

    experience = []

    experience_lines = sections[
        "experience"
    ]


    duration_pattern = re.compile(
        r"(?i)"
        r"(?:"
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
        r"[a-z]*\s+\d{4}"
        r"\s*[-–]\s*"
        r"(?:"
        r"present"
        r"|"
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
        r"[a-z]*\s+\d{4}"
        r")"
        r")"
        r"|"
        r"\b\d{4}\s*[-–]\s*"
        r"(?:\d{4}|present)\b"
    )


    current_experience = None


    for line in experience_lines:

        duration_match = (
            duration_pattern.search(line)
        )


        if duration_match:

            if current_experience:

                experience.append(
                    current_experience
                )


            duration = (
                duration_match.group(0)
            )


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

            if not current_experience[
                "company"
            ]:

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

    project_lines = sections[
        "projects"
    ]


    current_project = None


    for line in project_lines:

        if not line.strip():

            continue


        # ----------------------------------------------------
        # Bullet = description
        # ----------------------------------------------------

        if line.startswith(
            ("•", "-", "*")
        ):

            if current_project:

                description = (
                    line.lstrip(
                        "•-* "
                    ).strip()
                )

                current_project[
                    "description"
                ] += " " + description

            continue


        # ----------------------------------------------------
        # Determine if line is title
        # ----------------------------------------------------

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


            project_name = re.sub(
                r"\|.*",
                "",
                line
            ).strip()


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
        "the LLM service was unavailable."
    )


    # ========================================================
    # RETURN STRUCTURED DATA
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
# LLM + FALLBACK EXTRACTION
# ============================================================

def extract_resume_data(
    text: str
):

    """
    Attempts OpenAI LLM extraction first.

    If:
    - API key is missing
    - quota is exhausted
    - API returns an error
    - response is invalid

    then local extraction is automatically used.
    """

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )


    # ========================================================
    # NO API KEY
    # ========================================================

    if not api_key:

        print(
            "OPENAI_API_KEY not found."
        )

        print(
            "Using local resume extraction."
        )

        return (
            local_fallback_extraction(text),
            "local_fallback"
        )


    # ========================================================
    # TRY OPENAI
    # ========================================================

    try:

        from openai import OpenAI


        prompt = f"""
Extract the following resume into JSON only.

Use exactly this structure:

{{
  "summary": "short candidate summary",

  "skills": [
    "skill"
  ],

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
      "highlights": [""]
    }}
  ],

  "projects": [
    {{
      "name": "",
      "description": "",
      "technologies": [""]
    }}
  ],

  "certifications": [
    "certification"
  ]
}}

Rules:

- Extract only information explicitly present in the resume.
- Do not invent information.
- Use empty arrays if information is missing.
- Keep the extracted information concise.
- Return valid JSON only.

Resume:

{text[:15000]}
"""


        client = OpenAI(
            api_key=api_key
        )


        response = client.chat.completions.create(

            model=os.getenv(
                "OPENAI_MODEL",
                "gpt-4o-mini"
            ),

            messages=[

                {
                    "role": "system",

                    "content": (
                        "You are a resume parsing "
                        "assistant. Extract accurate "
                        "structured information without "
                        "inventing details."
                    )
                },

                {
                    "role": "user",

                    "content": prompt
                }
            ],

            response_format={
                "type": "json_object"
            },

            temperature=0
        )


        content = (
            response
            .choices[0]
            .message
            .content
        )


        if not content:

            raise ValueError(
                "LLM returned an empty response."
            )


        data = json.loads(
            content
        )


        print(
            "Resume extracted successfully "
            "using OpenAI."
        )


        return (
            data,
            "openai_llm"
        )


    # ========================================================
    # OPENAI ERROR → LOCAL FALLBACK
    # ========================================================

    except Exception as error:

        print(
            f"OpenAI extraction failed: {error}"
        )

        print(
            "Falling back to local "
            "resume extraction."
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

        (profile_id,)
    ).fetchone()


    if not profile:

        connection.close()

        raise HTTPException(

            status_code=404,

            detail="Profile not found."
        )


    # ========================================================
    # CHECK FILE TYPE
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


    with saved_path.open(
        "wb"
    ) as output_file:

        shutil.copyfileobj(
            file.file,
            output_file
        )


    # ========================================================
    # PARSE + EXTRACT
    # ========================================================

    try:

        resume_text = extract_text(
            saved_path
        )
        print("\n========== RESUME TEXT ==========")
        print(resume_text[:3000])
        print("========== END RESUME TEXT ==========\n")

        if not resume_text.strip():

            raise ValueError(
                "No readable text was found "
                "in this resume."
            )


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