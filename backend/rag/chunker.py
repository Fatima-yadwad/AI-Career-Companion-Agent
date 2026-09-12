from typing import List, Dict


def create_job_chunks(job: Dict) -> List[Dict]:
    """
    Convert one job posting into meaningful semantic chunks.

    Each chunk keeps the original job metadata so that
    retrieved chunks can be mapped back to the complete job.
    """

    chunks = []

    job_id = job.get("job_id", "")
    job_title = job.get("job_title", "")
    company = job.get("company", "")
    location = job.get("location", "")

    def add_chunk(section: str, text: str):
        if text and text.strip():
            chunks.append({
                "job_id": job_id,
                "job_title": job_title,
                "company": company,
                "location": location,
                "section": section,
                "text": text.strip()
            })

    add_chunk(
        "job_description",
        job.get("job_description", "")
    )

    responsibilities = job.get("responsibilities", [])
    if responsibilities:
        add_chunk(
            "responsibilities",
            "Responsibilities: " + "; ".join(responsibilities)
        )

    required_skills = job.get("required_skills", [])
    if required_skills:
        add_chunk(
            "required_skills",
            "Required skills: " + ", ".join(required_skills)
        )

    preferred_skills = job.get("preferred_skills", [])
    if preferred_skills:
        add_chunk(
            "preferred_skills",
            "Preferred skills: " + ", ".join(preferred_skills)
        )

    qualifications = job.get("qualifications", [])
    if qualifications:
        add_chunk(
            "qualifications",
            "Qualifications: " + "; ".join(qualifications)
        )

    add_chunk(
        "experience_requirements",
        job.get("experience_requirements", "")
    )

    add_chunk(
        "education_requirements",
        job.get("education_requirements", "")
    )

    return chunks