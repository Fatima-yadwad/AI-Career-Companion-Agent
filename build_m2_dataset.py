import pandas as pd
import json
import re
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CSV_PATH = BASE_DIR / "data" / "raw" / "linkdin_Job_data.csv" / "linkdin_Job_data.csv"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "internship_jobs.json"

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(CSV_PATH)

print("=" * 50)
print("M2 DATASET BUILDER")
print("=" * 50)
print(f"Original records: {len(df)}")


# ============================================================
# NORMALIZE
# ============================================================

for col in ["job", "company_name", "location", "work_type", "job_details"]:
    if col not in df.columns:
        df[col] = ""

    df[col] = df[col].fillna("").astype(str).str.strip()

df["title_clean"] = df["job"].str.lower()
df["details_clean"] = df["job_details"].str.lower()

df["combined"] = (
    df["title_clean"] + " " +
    df["details_clean"]
)


# ============================================================
# REMOVE EXACT DUPLICATES
# ============================================================

before = len(df)

df = df.drop_duplicates(
    subset=["job", "company_name", "location", "job_details"]
)

print(f"Exact duplicates removed: {before - len(df)}")


# ============================================================
# BAD / PROMOTIONAL / TRAINING TERMS
# ============================================================

training_terms = [
    "training fee",
    "training fees",
    "paid training",
    "guaranteed internship",
    "training + internship",
    "training+internship",
    "training and internship program",
    "industrial training",
    "course completion certificate",
    "course certificate",
    "self paced",
    "self-paced",
    "recorded sessions",
    "placement assistance",
    "job guarantee",
    "certificate program",
    "certification program",
    "bootcamp"
]

training_pattern = "|".join(
    re.escape(x) for x in training_terms
)

training_mask = df["combined"].str.contains(
    training_pattern,
    regex=True,
    case=False,
    na=False
)

print(f"Training/promotional removed: {training_mask.sum()}")

df = df[~training_mask].copy()


# ============================================================
# SENIOR / MANAGEMENT TERMS
# ============================================================

senior_terms = [
    "senior",
    "sr.",
    "sr ",
    "lead",
    "manager",
    "director",
    "head of",
    "principal",
    "vice president",
    "vp ",
    "chief",
    "architect"
]

senior_pattern = "|".join(
    re.escape(x) for x in senior_terms
)

senior_mask = df["title_clean"].str.contains(
    senior_pattern,
    regex=True,
    case=False,
    na=False
)

print(f"Senior/management removed: {senior_mask.sum()}")

df = df[~senior_mask].copy()


# ============================================================
# IRRELEVANT DOMAINS
# ============================================================

irrelevant_terms = [
    "human resources",
    "hr intern",
    "hr & recruitment",
    "recruitment",
    "talent acquisition",
    "digital marketing",
    "marketing intern",
    "sales intern",
    "sales executive",
    "business development",
    "business development intern",
    "public relations",
    "graphic design",
    "real estate",
    "customer support",
    "customer service",
    "telecaller",
    "content writer",
    "copywriter",
    "social media",
    "event management",
    "finance intern",
    "accounting intern"
]

irrelevant_pattern = "|".join(
    re.escape(x) for x in irrelevant_terms
)

irrelevant_mask = df["title_clean"].str.contains(
    irrelevant_pattern,
    regex=True,
    case=False,
    na=False
)

print(f"Irrelevant-domain removed: {irrelevant_mask.sum()}")

df = df[~irrelevant_mask].copy()


# ============================================================
# TECHNICAL DOMAIN TERMS
# ============================================================

technical_terms = {
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "react": "React",
    "angular": "Angular",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "django": "Django",
    "flask": "Flask",
    "html": "HTML",
    "css": "CSS",
    "sql": "SQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "postgresql": "PostgreSQL",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "artificial intelligence": "Artificial Intelligence",
    "computer vision": "Computer Vision",
    "natural language processing": "NLP",
    "nlp": "NLP",
    "data science": "Data Science",
    "data scientist": "Data Science",
    "data analyst": "Data Analytics",
    "data analysis": "Data Analytics",
    "data engineer": "Data Engineering",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "opencv": "OpenCV",
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "Google Cloud",
    "google cloud": "Google Cloud",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "devops": "DevOps",
    "cloud": "Cloud",
    "cybersecurity": "Cybersecurity",
    "cyber security": "Cybersecurity",
    "robotics": "Robotics",
    "android": "Android",
    "flutter": "Flutter",
    "blockchain": "Blockchain",
    "selenium": "Selenium",
    "qa": "QA",
    "testing": "Software Testing",
    "automation": "Automation"
}


def extract_skills(text):
    text = text.lower()
    found = []

    for keyword, display_name in technical_terms.items():
        if keyword in text and display_name not in found:
            found.append(display_name)

    return found


# ============================================================
# CLASSIFY INTERNSHIP / EARLY CAREER / TRAINEE
# ============================================================

intern_pattern = r"\bintern\b|\binternship\b|\binternships\b"

intern_mask = (
    df["title_clean"].str.contains(
        intern_pattern,
        regex=True,
        na=False
    )
)

# Early-career title indicators
early_title_pattern = (
    r"\bfresher\b|"
    r"\bentry[- ]level\b|"
    r"\btrainee\b|"
    r"\bjunior\b|"
    r"\bgraduate\b|"
    r"\bassociate\b"
)

early_title_mask = df["title_clean"].str.contains(
    early_title_pattern,
    regex=True,
    na=False
)

# Experience indicators suggesting an early-career role
early_details_pattern = (
    r"0\s*[-to]+\s*1\s*years?|"
    r"0\s*[-to]+\s*2\s*years?|"
    r"freshers?|"
    r"fresh graduates?|"
    r"recent graduates?|"
    r"entry level"
)

early_details_mask = df["details_clean"].str.contains(
    early_details_pattern,
    regex=True,
    na=False
)

early_mask = early_title_mask | (
    early_details_mask &
    ~intern_mask
)


# ============================================================
# TECHNICAL RELEVANCE
# ============================================================

df["skills"] = df["combined"].apply(extract_skills)

technical_mask = df["skills"].apply(len) > 0

df = df[technical_mask].copy()

print(f"Technical career records available: {len(df)}")


# Recalculate masks after filtering
df["is_internship"] = df["title_clean"].str.contains(
    intern_pattern,
    regex=True,
    na=False
)

df["is_early_career"] = (
    df["title_clean"].str.contains(
        early_title_pattern,
        regex=True,
        na=False
    )
    |
    df["details_clean"].str.contains(
        early_details_pattern,
        regex=True,
        na=False
    )
)


# ============================================================
# SCORE RECORDS
# ============================================================

def relevance_score(row):

    title = row["title_clean"]
    details = row["details_clean"]
    skills = row["skills"]

    score = 0

    # Strong internship signal
    if re.search(intern_pattern, title):
        score += 50

    # Early-career signal
    if re.search(early_title_pattern, title):
        score += 30

    if re.search(early_details_pattern, details):
        score += 15

    # Technical richness
    score += min(len(skills) * 3, 30)

    # Strong technical title signals
    technical_title_terms = [
        "software",
        "developer",
        "development",
        "python",
        "java",
        "machine learning",
        "artificial intelligence",
        "data science",
        "data analyst",
        "data engineer",
        "web",
        "cloud",
        "cybersecurity",
        "computer vision",
        "robotics",
        "devops",
        "testing",
        "automation"
    ]

    for term in technical_title_terms:
        if term in title:
            score += 5

    return score


df["relevance_score"] = df.apply(
    relevance_score,
    axis=1
)


# ============================================================
# REMOVE SUSPICIOUS NON-INTERNSHIP TITLES
# ============================================================

bad_titles = [
    "training specialist",
    "trainer",
    "training coordinator",
    "strategy & partnerships",
    "partnerships",
    "business analyst",
    "account manager",
    "sales",
    "marketing",
    "recruiter",
    "recruitment"
]

bad_title_pattern = "|".join(
    re.escape(x) for x in bad_titles
)

bad_title_mask = df["title_clean"].str.contains(
    bad_title_pattern,
    regex=True,
    na=False
)

df = df[~bad_title_mask].copy()


# ============================================================
# REMOVE CONTENT DUPLICATES
# ============================================================

df["dedup_key"] = (
    df["title_clean"]
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
    + "|"
    + df["company_name"].str.lower()
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

before = len(df)

df = df.drop_duplicates(
    subset=["dedup_key"]
)

print(f"Similar title/company duplicates removed: {before - len(df)}")


# ============================================================
# SELECT DATASET
# ============================================================

internships = df[
    df["is_internship"]
].sort_values(
    "relevance_score",
    ascending=False
)

early_career = df[
    (~df["is_internship"]) &
    (df["is_early_career"])
].sort_values(
    "relevance_score",
    ascending=False
)

print(f"Technical internships available: {len(internships)}")
print(f"Technical early-career/trainee available: {len(early_career)}")


# We want a balanced knowledge base.
# First take the strongest internships.
intern_count = min(len(internships), 100)

selected_internships = internships.head(
    intern_count
)

remaining_needed = 180 - len(selected_internships)

selected_early = early_career.head(
    max(0, remaining_needed)
)

selected = pd.concat(
    [selected_internships, selected_early],
    ignore_index=True
)


# If fewer than 150 are available, report it honestly.
if len(selected) < 150:

    print()
    print("WARNING:")
    print(
        f"Only {len(selected)} high-quality technical "
        "internship/early-career records were found."
    )
    print(
        "No synthetic jobs will be created."
    )

elif len(selected) > 200:

    selected = selected.head(200)


# ============================================================
# BUILD STANDARDIZED JSON
# ============================================================

records = []

for index, row in selected.iterrows():

    title = row["job"]
    company = row["company_name"]
    location = row["location"]
    details = row["job_details"]
    work_type = row["work_type"]

    if row["is_internship"]:
        career_type = "Internship"
    elif re.search(
        r"\btrainee\b",
        row["title_clean"]
    ):
        career_type = "Trainee"
    else:
        career_type = "Early Career"

    # Create a clean description
    description = re.sub(
        r"\s+",
        " ",
        details
    ).strip()

    # Limit extremely long descriptions
    description = description[:5000]

    # Basic section extraction
    responsibilities = []
    qualifications = []

    sentences = re.split(
        r"[.\n]",
        description
    )

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        low = sentence.lower()

        if any(
            word in low
            for word in [
                "responsible",
                "develop",
                "design",
                "build",
                "implement",
                "maintain",
                "work on",
                "assist"
            ]
        ):
            responsibilities.append(sentence)

        if any(
            word in low
            for word in [
                "require",
                "qualification",
                "degree",
                "bachelor",
                "education",
                "experience",
                "knowledge"
            ]
        ):
            qualifications.append(sentence)

    record = {
        "job_id": f"JOB{len(records) + 1:03d}",
        "job_title": title,
        "company": company,
        "location": location,
        "job_type": career_type,
        "work_type": work_type,
        "job_description": description,
        "responsibilities": responsibilities[:10],
        "required_skills": row["skills"],
        "preferred_skills": [],
        "qualifications": qualifications[:10],
        "experience_requirements": "",
        "education_requirements": "",
        "duration": "",
        "source": "Kaggle LinkedIn Job Dataset - Curated",
        "source_original_job_id": str(row["job_ID"])
    }

    records.append(record)


# ============================================================
# SAVE
# ============================================================

with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        records,
        f,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# REPORT
# ============================================================

internship_total = sum(
    1 for x in records
    if x["job_type"] == "Internship"
)

early_total = sum(
    1 for x in records
    if x["job_type"] == "Early Career"
)

trainee_total = sum(
    1 for x in records
    if x["job_type"] == "Trainee"
)


print()
print("=" * 50)
print("M2 CURATED KNOWLEDGE BASE")
print("=" * 50)

print(f"Final records: {len(records)}")
print(f"Internships: {internship_total}")
print(f"Early Career: {early_total}")
print(f"Trainee: {trainee_total}")

print()
print(f"Output: {OUTPUT_PATH}")

print("=" * 50)
print()
print("SELECTED JOBS:")

for i, record in enumerate(records[:40], 1):

    print(
        f"{i}. "
        f"[{record['job_type']}] "
        f"{record['job_title']} | "
        f"{record['company']} | "
        f"{record['location']} | "
        f"{', '.join(record['required_skills'])}"
    )

print()
print("=" * 50)