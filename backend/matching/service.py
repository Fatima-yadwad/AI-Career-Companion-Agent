from typing import Dict, Any

from backend.rag.retriever import JobRetriever
from backend.matching.job_loader import get_jobs_by_id
from backend.matching.matcher import calculate_job_match


class MatchingService:

    def __init__(self):
        self.retriever = JobRetriever()

    def match_candidate(
        self,
        candidate: Dict[str, Any],
        top_k: int = 5
    ):

        query_parts = []

        if candidate.get("summary"):
            query_parts.append(
                candidate["summary"]
            )

        skills = candidate.get("skills", [])

        if skills:
            query_parts.append(
                "Skills: " + ", ".join(skills)
            )

        target_role = candidate.get(
            "target_role",
            ""
        )

        if target_role:
            query_parts.append(
                "Target role: " + target_role
            )

        query = " ".join(query_parts)

        retrieved = self.retriever.search(
            query,
            top_k=min(max(top_k * 3, 5), 20)
        )

        # Deduplicate jobs because multiple chunks
        # from the same job may be retrieved.
        unique_jobs = {}

        for result in retrieved:
            job_id = result.get("job_id")

            if job_id and job_id not in unique_jobs:
                unique_jobs[job_id] = result

        job_ids = list(unique_jobs.keys())

        jobs = get_jobs_by_id(job_ids)

        results = []

        for job in jobs:

            retrieval_result = unique_jobs.get(
                job.get("job_id"),
                {}
            )

            result = calculate_job_match(
                candidate,
                job,
                retrieval_similarity=
                    retrieval_result.get(
                        "similarity",
                        0.0
                    )
            )

            results.append(result)

        results.sort(
            key=lambda item: item["match_score"],
            reverse=True
        )

        return results[:top_k]