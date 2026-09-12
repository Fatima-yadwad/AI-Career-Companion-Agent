import json
import sys
from pathlib import Path

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.matching.service import MatchingService


# ============================================================
# PATHS
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
# LOAD JSON
# ============================================================

def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# BUILD CANDIDATE INPUT
# ============================================================

def build_candidate(profile):
    """
    Convert evaluation profile into the structure expected
    by MatchingService.match_candidate().
    """

    return {
        "summary": profile.get("summary", ""),
        "skills": profile.get("skills", []),
        "target_role": profile.get("target_role", ""),
        "education": profile.get("education", []),
        "experience": profile.get("experience", []),
        "projects": profile.get("projects", []),
        "certifications": profile.get("certifications", [])
    }


# ============================================================
# DISPLAY MATCH RESULT
# ============================================================

def display_result(rank, result):

    print(f"\n{rank}. {result.get('job_title', 'Unknown Job')}")

    print(
        f"   Company: "
        f"{result.get('company', 'Unknown')}"
    )

    print(
        f"   Location: "
        f"{result.get('location', 'Unknown')}"
    )

    print(
        f"   Match Score: "
        f"{result.get('match_score', 'N/A')}"
    )

    print(
        f"   Retrieval Similarity: "
        f"{result.get('retrieval_similarity', 'N/A')}"
    )

    # --------------------------------------------------------
    # Skills
    # --------------------------------------------------------

    required = result.get(
        "required_skills_matched",
        result.get("matched_required_skills", [])
    )

    missing = result.get(
        "required_skills_missing",
        result.get("missing_required_skills", [])
    )

    preferred = result.get(
        "preferred_skills_matched",
        result.get("matched_preferred_skills", [])
    )

    if required:
        print(
            "   Required Skills Matched: "
            + ", ".join(map(str, required))
        )

    if missing:
        print(
            "   Required Skills Missing: "
            + ", ".join(map(str, missing))
        )

    if preferred:
        print(
            "   Preferred Skills Matched: "
            + ", ".join(map(str, preferred))
        )

    # --------------------------------------------------------
    # Reasoning
    # --------------------------------------------------------

    reasoning = result.get(
        "reasoning",
        result.get(
            "match_reasoning",
            result.get("explanation", "")
        )
    )

    if reasoning:
        print(f"   Reasoning: {reasoning}")


# ============================================================
# MAIN EVALUATION
# ============================================================

def main():

    print("=" * 80)
    print("AI CAREER COMPANION")
    print("M2.4 JOB-RESUME MATCHING AGENT EVALUATION")
    print("=" * 80)

    # --------------------------------------------------------
    # 1. Profiles
    # --------------------------------------------------------

    print("\n[1/3] Loading sample profiles...")

    profiles = load_json(PROFILES_PATH)

    print(f"Profiles loaded: {len(profiles)}")

    # --------------------------------------------------------
    # 2. Jobs
    # --------------------------------------------------------

    print("\n[2/3] Loading job dataset...")

    jobs = load_json(JOBS_PATH)

    print(f"Jobs available: {len(jobs)}")

    # --------------------------------------------------------
    # 3. Matching service
    # --------------------------------------------------------

    print("\n[3/3] Initializing Matching Service...")

    matching_service = MatchingService()

    print("Matching Service initialized successfully.")

    # --------------------------------------------------------
    # Evaluation counters
    # --------------------------------------------------------

    total_results = 0
    all_scores = []

    profiles_with_results = 0

    # --------------------------------------------------------
    # Evaluate each student
    # --------------------------------------------------------

    for profile in profiles:

        student_id = profile.get(
            "student_id",
            profile.get("id", "UNKNOWN")
        )

        student_name = profile.get(
            "name",
            profile.get("full_name", "Unknown Student")
        )

        target_role = profile.get(
            "target_role",
            ""
        )

        print("\n" + "=" * 80)
        print(f"PROFILE: {student_id}")
        print(f"STUDENT: {student_name}")
        print(f"TARGET ROLE: {target_role}")
        print("=" * 80)

        try:

            candidate = build_candidate(profile)

            # IMPORTANT:
            # MatchingService uses match_candidate()
            results = matching_service.match_candidate(
                candidate,
                top_k=5
            )

            if not results:
                print("\nNo matching jobs returned.")
                continue

            profiles_with_results += 1
            total_results += len(results)

            # ------------------------------------------------
            # Display results
            # ------------------------------------------------

            for rank, result in enumerate(
                results,
                start=1
            ):

                display_result(
                    rank,
                    result
                )

                score = result.get(
                    "match_score"
                )

                if isinstance(
                    score,
                    (int, float)
                ):
                    all_scores.append(
                        float(score)
                    )

        except Exception as error:

            print(
                f"\nERROR while evaluating profile: "
                f"{error}"
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n")
    print("=" * 80)
    print("M2.4 MATCHING AGENT EVALUATION SUMMARY")
    print("=" * 80)

    print(
        f"\nProfiles tested: "
        f"{len(profiles)}"
    )

    print(
        f"Profiles with results: "
        f"{profiles_with_results}"
    )

    print(
        f"Jobs in knowledge base: "
        f"{len(jobs)}"
    )

    print(
        f"Matching results evaluated: "
        f"{total_results}"
    )

    # --------------------------------------------------------
    # Score statistics
    # --------------------------------------------------------

    if all_scores:

        print("\nMatch Score Statistics")

        print(
            f"Minimum score: "
            f"{min(all_scores):.2f}"
        )

        print(
            f"Maximum score: "
            f"{max(all_scores):.2f}"
        )

        print(
            f"Average score: "
            f"{sum(all_scores) / len(all_scores):.2f}"
        )

    else:

        print(
            "\nNo numeric match scores were detected."
        )

    print("\n" + "=" * 80)
    print("M2.4 EVALUATION COMPLETE")
    print("=" * 80)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()