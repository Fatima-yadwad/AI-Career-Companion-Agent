import json
import sys
from pathlib import Path

import faiss
import numpy as np


# ============================================================
# PATH CONFIGURATION
# ============================================================

# Project root:
# D:\infosys\ai-career-companion
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Allow imports from the project root when this file is
# executed directly with:
# python backend\rag\vector_store.py
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.rag.loader import load_jobs
from backend.rag.chunker import create_job_chunks
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
# BUILD VECTOR STORE
# ============================================================

def build_vector_store():
    print("=" * 60)
    print("M2.2 RAG VECTOR STORE BUILDER")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Load curated jobs
    # --------------------------------------------------------

    print("\n[1/5] Loading jobs...")

    jobs = load_jobs()

    print(f"Jobs loaded: {len(jobs)}")

    if not jobs:
        raise ValueError("No jobs found in the dataset.")

    # --------------------------------------------------------
    # 2. Create semantic chunks
    # --------------------------------------------------------

    print("\n[2/5] Creating semantic job chunks...")

    all_chunks = []

    for job in jobs:
        chunks = create_job_chunks(job)
        all_chunks.extend(chunks)

    print(f"Total chunks created: {len(all_chunks)}")

    if not all_chunks:
        raise ValueError("No chunks were created from the job dataset.")

    # --------------------------------------------------------
    # 3. Generate embeddings
    # --------------------------------------------------------

    print("\n[3/5] Generating embeddings...")

    texts = [
        chunk["text"]
        for chunk in all_chunks
    ]

    embedding_model = EmbeddingModel()

    embeddings = embedding_model.encode(texts)

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    print(f"Embedding matrix shape: {embeddings.shape}")

    # --------------------------------------------------------
    # 4. Build FAISS index
    # --------------------------------------------------------

    print("\n[4/5] Building FAISS index...")

    dimension = embeddings.shape[1]

    print(f"Embedding dimension: {dimension}")

    # IndexFlatIP = Inner Product similarity.
    #
    # Because embeddings are normalized in embeddings.py,
    # Inner Product behaves like cosine similarity.
    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    print(f"Vectors added to FAISS: {index.ntotal}")

    # --------------------------------------------------------
    # 5. Save index + metadata
    # --------------------------------------------------------

    print("\n[5/5] Saving vector store...")

    VECTOR_STORE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    faiss.write_index(
        index,
        str(INDEX_PATH)
    )

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            all_chunks,
            file,
            indent=2,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("FAISS VECTOR STORE CREATED SUCCESSFULLY")
    print("=" * 60)

    print(f"Jobs:              {len(jobs)}")
    print(f"Chunks:             {len(all_chunks)}")
    print(f"Vectors:            {index.ntotal}")
    print(f"Dimensions:         {dimension}")
    print(f"FAISS index:        {INDEX_PATH}")
    print(f"Metadata:           {METADATA_PATH}")

    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    build_vector_store()