import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "internship_jobs.json"
)


def load_all_jobs():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Job dataset not found: {DATASET_PATH}"
        )

    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        jobs = json.load(file)

    if not isinstance(jobs, list):
        raise ValueError("Job dataset must contain a JSON list.")

    return jobs


def get_jobs_by_id(job_ids):
    jobs = load_all_jobs()

    job_map = {
        job.get("job_id"): job
        for job in jobs
    }

    return [
        job_map[job_id]
        for job_id in job_ids
        if job_id in job_map
    ]