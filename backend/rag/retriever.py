import json
import sys
from pathlib import Path

import faiss


# ============================================================
# PATH CONFIGURATION
# ============================================================

# Project root:
# D:\infosys\ai-career-companion
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Allow imports when this file is executed directly:
# python backend\rag\retriever.py
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.rag.embeddings import EmbeddingModel


# ============================================================
# VECTOR STORE PATHS
# ============================================================

VECTOR_STORE_DIR = (
    PROJECT_ROOT
    / "backend"
    / "data"
    / "vector_store"
)

INDEX_PATH = VECTOR_STORE_DIR / "jobs.index"
METADATA_PATH = VECTOR_STORE_DIR / "metadata.json"


# ============================================================
# JOB RETRIEVER
# ============================================================

class JobRetriever:

    def __init__(self):

        if not INDEX_PATH.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {INDEX_PATH}"
            )

        if not METADATA_PATH.exists():
            raise FileNotFoundError(
                f"Metadata file not found: {METADATA_PATH}"
            )

        print("Loading FAISS index...")

        self.index = faiss.read_index(
            str(INDEX_PATH)
        )

        print(
            f"FAISS vectors loaded: "
            f"{self.index.ntotal}"
        )

        with open(
            METADATA_PATH,
            "r",
            encoding="utf-8"
        ) as file:
            self.metadata = json.load(file)

        if self.index.ntotal != len(self.metadata):
            raise ValueError(
                "FAISS index and metadata size do not match."
            )

        print(
            f"Metadata records loaded: "
            f"{len(self.metadata)}"
        )

        self.embedding_model = EmbeddingModel()

    # ========================================================
    # SEMANTIC SEARCH
    # ========================================================

    def search(
        self,
        query: str,
        top_k: int = 5
    ):

        if not query or not query.strip():
            return []

        # Prevent requesting more results than available
        top_k = min(
            max(1, top_k),
            self.index.ntotal
        )

        # Convert natural-language query into
        # a 384-dimensional embedding
        query_embedding = (
            self.embedding_model.encode_query(
                query
            )
        )

        # FAISS expects:
        # (number_of_queries, embedding_dimension)
        query_embedding = query_embedding.reshape(
            1,
            -1
        )

        # Search using inner-product similarity.
        # Our embeddings are normalized, so this
        # corresponds to cosine similarity.
        scores, indices = self.index.search(
            query_embedding,
            top_k
        )

        results = []

        for score, index_id in zip(
            scores[0],
            indices[0]
        ):

            if index_id < 0:
                continue

            metadata = self.metadata[index_id]

            results.append({
                "job_id": metadata.get(
                    "job_id"
                ),
                "job_title": metadata.get(
                    "job_title"
                ),
                "company": metadata.get(
                    "company"
                ),
                "location": metadata.get(
                    "location"
                ),
                "section": metadata.get(
                    "section"
                ),
                "text": metadata.get(
                    "text"
                ),
                "similarity": round(
                    float(score),
                    4
                )
            })

        return results


# ============================================================
# COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":

    retriever = JobRetriever()

    query = (
        "Python machine learning "
        "internship with TensorFlow"
    )

    print()
    print("=" * 60)
    print("SEMANTIC SEARCH TEST")
    print("=" * 60)
    print(f"Query: {query}")
    print()

    results = retriever.search(
        query,
        top_k=5
    )

    for rank, result in enumerate(
        results,
        start=1
    ):

        print(
            f"{rank}. "
            f"{result['job_title']} | "
            f"{result['company']}"
        )

        print(
            f"   Job ID: "
            f"{result['job_id']}"
        )

        print(
            f"   Location: "
            f"{result['location']}"
        )

        print(
            f"   Section: "
            f"{result['section']}"
        )

        print(
            f"   Similarity: "
            f"{result['similarity']}"
        )

        print()