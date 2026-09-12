import re
from typing import Dict, List, Any


# ============================================================
# SKILL NORMALIZATION
# ============================================================

SKILL_ALIASES = {
    "ml": "machine learning",
    "machine-learning": "machine learning",
    "dl": "deep learning",
    "ai": "artificial intelligence",
    "cv": "computer vision",
    "nlp": "natural language processing",
    "js": "javascript",
    "ts": "typescript",
    "postgres": "postgresql",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
}


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^a-z0-9+#.\-/ ]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_skill(skill: str) -> str:
    skill = normalize_text(skill)

    return SKILL_ALIASES.get(skill, skill)


# ============================================================
# SKILL EXTRACTION
# ============================================================

def normalize_skill_list(skills: List[str]) -> set:
    normalized = set()

    for skill in skills or []:
        value = normalize_skill(skill)

        if value:
            normalized.add(value)

    return normalized


def get_candidate_skills(candidate: Dict[str, Any]) -> set:
    """
    Extract skills from the structured candidate profile.
    """

    skills = candidate.get("skills", [])

    return normalize_skill_list(skills)


def get_job_required_skills(job: Dict[str, Any]) -> set:
    return normalize_skill_list(
        job.get("required_skills", [])
    )


def get_job_preferred_skills(job: Dict[str, Any]) -> set:
    return normalize_skill_list(
        job.get("preferred_skills", [])
    )


# ============================================================
# SKILL MATCHING
# ============================================================

def calculate_skill_match(
    candidate_skills: set,
    job_skills: set
) -> Dict[str, Any]:

    if not job_skills:
        return {
            "score": 100.0,
            "matched": [],
            "missing": []
        }

    matched = sorted(
        candidate_skills.intersection(job_skills)
    )

    missing = sorted(
        job_skills.difference(candidate_skills)
    )

    score = (
        len(matched) / len(job_skills)
    ) * 100

    return {
        "score": round(score, 2),
        "matched": matched,
        "missing": missing
    }


# ============================================================
# PROJECT RELEVANCE
# ============================================================

def get_project_text(candidate: Dict[str, Any]) -> str:

    projects = candidate.get("projects", [])

    parts = []

    for project in projects:

        if isinstance(project, dict):

            parts.append(
                str(project.get("name", ""))
            )

            parts.append(
                str(project.get("description", ""))
            )

            technologies = project.get(
                "technologies",
                []
            )

            parts.extend(
                str(technology)
                for technology in technologies
            )

    return normalize_text(
        " ".join(parts)
    )


def calculate_project_match(
    candidate: Dict[str, Any],
    job: Dict[str, Any]
) -> float:

    project_text = get_project_text(candidate)

    if not project_text:
        return 0.0

    job_text = normalize_text(
        " ".join(
            [
                str(job.get("job_description", "")),
                " ".join(
                    job.get("responsibilities", [])
                ),
                " ".join(
                    job.get("required_skills", [])
                ),
                " ".join(
                    job.get("preferred_skills", [])
                ),
            ]
        )
    )

    candidate_skills = get_candidate_skills(candidate)

    if not candidate_skills:
        return 0.0

    relevant_skills = [
        skill
        for skill in candidate_skills
        if skill in job_text
    ]

    if not relevant_skills:
        return 0.0

    return round(
        min(
            100.0,
            (len(relevant_skills) /
             len(candidate_skills)) * 100
        ),
        2
    )


# ============================================================
# EDUCATION MATCH
# ============================================================

def calculate_education_match(
    candidate: Dict[str, Any],
    job: Dict[str, Any]
) -> float:

    education = candidate.get(
        "education",
        []
    )

    if not education:
        return 0.0

    candidate_text = normalize_text(
        " ".join(
            str(item)
            for item in education
        )
    )

    job_text = normalize_text(
        str(
            job.get(
                "education_requirements",
                ""
            )
        )
    )

    if not job_text:
        return 100.0

    education_keywords = [
        "bachelor",
        "b.tech",
        "b.e",
        "engineering",
        "computer science",
        "information technology",
        "artificial intelligence",
        "machine learning",
        "master",
        "m.tech",
        "m.s"
    ]

    matches = [
        keyword
        for keyword in education_keywords
        if keyword in candidate_text
        and keyword in job_text
    ]

    if matches:
        return 100.0

    # If the job simply requires a degree and
    # candidate has an education record.
    if "degree" in job_text or "bachelor" in job_text:
        return 75.0

    return 50.0


# ============================================================
# EXPERIENCE MATCH
# ============================================================

def calculate_experience_match(
    candidate: Dict[str, Any],
    job: Dict[str, Any]
) -> float:

    experience = candidate.get(
        "experience",
        []
    )

    job_experience = normalize_text(
        str(
            job.get(
                "experience_requirements",
                ""
            )
        )
    )

    # Internship / fresher roles
    if not job_experience:
        return 100.0

    if not experience:
        if any(
            keyword in job_experience
            for keyword in [
                "intern",
                "fresher",
                "entry level",
                "student",
                "0 year"
            ]
        ):
            return 100.0

        return 25.0

    return 100.0


# ============================================================
# QUALIFICATION MATCH
# ============================================================

def calculate_qualification_match(
    candidate: Dict[str, Any],
    job: Dict[str, Any]
) -> float:

    qualifications = job.get(
        "qualifications",
        []
    )

    if not qualifications:
        return 100.0

    candidate_text = normalize_text(
        str(candidate)
    )

    matches = 0

    for qualification in qualifications:

        qualification_text = normalize_text(
            str(qualification)
        )

        if not qualification_text:
            continue

        words = qualification_text.split()

        relevant_words = [
            word
            for word in words
            if len(word) > 3
        ]

        if any(
            word in candidate_text
            for word in relevant_words
        ):
            matches += 1

    if not qualifications:
        return 100.0

    return round(
        (matches / len(qualifications)) * 100,
        2
    )


# ============================================================
# COMPLETE JOB MATCH
# ============================================================

def calculate_job_match(
    candidate: Dict[str, Any],
    job: Dict[str, Any],
    retrieval_similarity: float = 0.0
) -> Dict[str, Any]:

    candidate_skills = get_candidate_skills(
        candidate
    )

    required_skills = get_job_required_skills(
        job
    )

    preferred_skills = get_job_preferred_skills(
        job
    )

    required_result = calculate_skill_match(
        candidate_skills,
        required_skills
    )

    preferred_result = calculate_skill_match(
        candidate_skills,
        preferred_skills
    )

    project_score = calculate_project_match(
        candidate,
        job
    )

    education_score = calculate_education_match(
        candidate,
        job
    )

    experience_score = calculate_experience_match(
        candidate,
        job
    )

    qualification_score = calculate_qualification_match(
        candidate,
        job
    )

    # ========================================================
    # WEIGHTED MATCH SCORE
    # ========================================================

    match_score = (
        0.40 * required_result["score"]
        + 0.15 * preferred_result["score"]
        + 0.15 * project_score
        + 0.10 * education_score
        + 0.10 * experience_score
        + 0.10 * qualification_score
    )

    match_score = round(
        min(100.0, match_score),
        2
    )

    # ========================================================
    # REASONING
    # ========================================================

    matched_skills = sorted(
        set(required_result["matched"])
        | set(preferred_result["matched"])
    )

    missing_skills = sorted(
        set(required_result["missing"])
    )

    reasoning_parts = []

    if matched_skills:
        reasoning_parts.append(
            "The candidate matches key skills including "
            + ", ".join(matched_skills[:6])
            + "."
        )

    if missing_skills:
        reasoning_parts.append(
            "Important missing required skills include "
            + ", ".join(missing_skills[:5])
            + "."
        )

    if project_score >= 70:
        reasoning_parts.append(
            "The candidate's projects show strong relevance "
            "to this role."
        )
    elif project_score >= 40:
        reasoning_parts.append(
            "The candidate has some project experience "
            "relevant to this role."
        )

    if education_score >= 75:
        reasoning_parts.append(
            "The candidate's education appears compatible "
            "with the role."
        )

    if experience_score >= 75:
        reasoning_parts.append(
            "The candidate's experience level is suitable "
            "for the position."
        )

    if not reasoning_parts:
        reasoning_parts.append(
            "The role has limited overlap with the "
            "available candidate information."
        )

    reasoning = " ".join(reasoning_parts)

    return {
        "job_id": job.get("job_id"),
        "job_title": job.get("job_title"),
        "company": job.get("company"),
        "location": job.get("location"),
        "work_type": job.get("work_type"),

        "match_score": match_score,

        "matched_skills": matched_skills,
        "missing_skills": missing_skills,

        "required_skill_score": required_result["score"],
        "preferred_skill_score": preferred_result["score"],
        "project_score": project_score,
        "education_score": education_score,
        "experience_score": experience_score,
        "qualification_score": qualification_score,

        "retrieval_similarity": round(
            float(retrieval_similarity),
            4
        ),

        "reasoning": reasoning
    }