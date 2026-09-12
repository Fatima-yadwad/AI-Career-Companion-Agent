import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "internship_jobs.json"


def load_jobs():
    """Load curated internship/job postings from the M2 dataset."""

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Job dataset not found: {DATASET_PATH}"
        )

    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        jobs = json.load(file)

    if not isinstance(jobs, list):
        raise ValueError("Job dataset must contain a JSON list.")

    return jobs


if __name__ == "__main__":
    jobs = load_jobs()

    print(f"Loaded jobs: {len(jobs)}")

    if jobs:
        print("First job:")
        print(jobs[0])