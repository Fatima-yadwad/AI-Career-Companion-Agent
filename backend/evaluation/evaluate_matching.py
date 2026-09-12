import json
import sys
from pathlib import Path


# ============================================================
# PATH CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT RAG + MATCHING SERVICES
# ============================================================

from backend.rag.retriever import JobRetriever


# ============================================================
# FILE PATHS
# ============================================================

PROFILES_PATH = (
    PROJECT_ROOT
    / "backend"
    / "evaluation"
    / "sample_profiles.json"
)

JOBS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "internship_jobs.json"
)


# ============================================================
# LOAD SAMPLE PROFILES
# ============================================================

def load_profiles():
    if not PROFILES_PATH.exists():
        raise FileNotFoundError(
            f"Sample profiles not found: {PROFILES_PATH}"
        )

    with open(PROFILES_PATH, "r", encoding="utf-8") as file:
        profiles = json.load(file)

    if not isinstance(profiles, list):
        raise ValueError(
            "sample_profiles.json must contain a JSON list."
        )

    return profiles


# ============================================================
# LOAD JOB DATA
# ============================================================

def load_jobs():
    if not JOBS_PATH.exists():
        raise FileNotFoundError(
            f"Job dataset not found: {JOBS_PATH}"
        )

    with open(JOBS_PATH, "r", encoding="utf-8") as file:
        jobs = json.load(file)

    if not isinstance(jobs, list):
        raise ValueError(
            "internship_jobs.json must contain a JSON list."
        )

    return jobs


# ============================================================
# BUILD SEARCH QUERY
# ============================================================

def build_profile_query(profile):
    parts = [
        profile.get("target_role", ""),
        " ".join(profile.get("skills", [])),
        " ".join(profile.get("projects", [])),
        profile.get("education", "")
    ]

    return " ".join(
        part.strip()
        for part in parts
        if part and part.strip()
    )


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text):
    if not text:
        return ""

    return " ".join(
        str(text).lower().strip().split()
    )


# ============================================================
# CHECK RELEVANCE
# ============================================================

def is_relevant(profile, result):
    """
    Determines whether a retrieved job is relevant
    to the student's target role or skills.

    This is an evaluation heuristic, not the production
    matching score.
    """

    job_text = normalize_text(
        " ".join(
            [
                result.get("job_title", ""),
                result.get("company", ""),
                result.get("text", "")
            ]
        )
    )

    target_role = normalize_text(
        profile.get("target_role", "")
    )

    skills = [
        normalize_text(skill)
        for skill in profile.get("skills", [])
    ]

    # Target role keyword overlap
    role_words = [
        word
        for word in target_role.split()
        if len(word) > 2
    ]

    role_match = any(
        word in job_text
        for word in role_words
    )

    # Skill overlap
    skill_match = any(
        skill and skill in job_text
        for skill in skills
    )

    return role_match or skill_match


# ============================================================
# CALCULATE RETRIEVAL METRICS
# ============================================================

def calculate_retrieval_metrics(profile_results):
    total_profiles = len(profile_results)

    top1_relevant = 0
    top3_relevant = 0
    top5_relevant = 0

    for item in profile_results:

        results = item["results"]

        if not results:
            continue

        # Top-1
        if is_relevant(item["profile"], results[0]):
            top1_relevant += 1

        # Top-3
        top3_results = results[:3]

        if any(
            is_relevant(item["profile"], result)
            for result in top3_results
        ):
            top3_relevant += 1

        # Top-5
        top5_results = results[:5]

        if any(
            is_relevant(item["profile"], result)
            for result in top5_results
        ):
            top5_relevant += 1

    if total_profiles == 0:
        return {
            "top1": 0,
            "top3": 0,
            "top5": 0
        }

    return {
        "top1": round(
            (top1_relevant / total_profiles) * 100,
            2
        ),
        "top3": round(
            (top3_relevant / total_profiles) * 100,
            2
        ),
        "top5": round(
            (top5_relevant / total_profiles) * 100,
            2
        )
    }


# ============================================================
# MAIN EVALUATION
# ============================================================

def main():

    print("=" * 80)
    print("AI CAREER COMPANION")
    print("M2.4 RAG RETRIEVAL EVALUATION")
    print("=" * 80)

    print("\n[1/4] Loading sample profiles...")

    profiles = load_profiles()

    print(f"Profiles loaded: {len(profiles)}")

    print("\n[2/4] Loading job dataset...")

    jobs = load_jobs()

    print(f"Jobs available: {len(jobs)}")

    print("\n[3/4] Loading FAISS retriever...")

    retriever = JobRetriever()

    print("\n[4/4] Running evaluation...")

    profile_results = []

    # ========================================================
    # TEST EACH PROFILE
    # ========================================================

    for profile in profiles:

        profile_id = profile.get(
            "profile_id",
            "UNKNOWN"
        )

        name = profile.get(
            "name",
            "Unknown Student"
        )

        target_role = profile.get(
            "target_role",
            ""
        )

        query = build_profile_query(profile)

        print("\n")
        print("=" * 80)
        print(f"PROFILE: {profile_id}")
        print(f"STUDENT: {name}")
        print(f"TARGET ROLE: {target_role}")
        print("=" * 80)

        print("\nSearch Query:")
        print(query)

        # Retrieve more than 5 chunks so that we can
        # inspect the top 5 unique jobs.
        retrieved = retriever.search(
            query,
            top_k=15
        )

        # ----------------------------------------------------
        # REMOVE DUPLICATE JOBS
        # ----------------------------------------------------

        unique_jobs = {}
        
        for result in retrieved:

            job_id = result.get("job_id")

            if job_id not in unique_jobs:
                unique_jobs[job_id] = result

        results = list(
            unique_jobs.values()
        )[:5]

        print("\nTop-5 Retrieved Jobs:")

        if not results:
            print("No results found.")

        for rank, result in enumerate(
            results,
            start=1
        ):

            relevant = is_relevant(
                profile,
                result
            )

            relevance_label = (
                "RELEVANT"
                if relevant
                else "CHECK"
            )

            print(
                f"\n{rank}. "
                f"{result.get('job_title', 'Unknown')}"
            )

            print(
                f"   Company: "
                f"{result.get('company', 'Unknown')}"
            )

            print(
                f"   Location: "
                f"{result.get('location', 'Unknown')}"
            )

            print(
                f"   Similarity: "
                f"{result.get('similarity', 0)}"
            )

            print(
                f"   Section: "
                f"{result.get('section', 'Unknown')}"
            )

            print(
                f"   Relevance: "
                f"{relevance_label}"
            )

        profile_results.append(
            {
                "profile": profile,
                "results": results
            }
        )

    # ========================================================
    # RETRIEVAL METRICS
    # ========================================================

    metrics = calculate_retrieval_metrics(
        profile_results
    )

    print("\n")
    print("=" * 80)
    print("M2.4 RETRIEVAL EVALUATION SUMMARY")
    print("=" * 80)

    print(
        f"\nProfiles tested: "
        f"{len(profiles)}"
    )

    print(
        f"Jobs in knowledge base: "
        f"{len(jobs)}"
    )

    print(
        f"\nTop-1 relevance: "
        f"{metrics['top1']}%"
    )

    print(
        f"Top-3 relevance: "
        f"{metrics['top3']}%"
    )

    print(
        f"Top-5 relevance: "
        f"{metrics['top5']}%"
    )

    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()