import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.retriever import JobRetriever


def main():
    print("=" * 70)
    print("M2.2 RAG RETRIEVAL EVALUATION")
    print("=" * 70)

    retriever = JobRetriever()

    test_queries = [
        "Python machine learning internship with TensorFlow",
        "React frontend development internship",
        "Data science internship using Python SQL and Pandas",
        "Cloud internship using AWS",
        "Cybersecurity trainee role"
    ]

    for query in test_queries:
        print("\n" + "=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)

        results = retriever.search(query, top_k=3)

        if not results:
            print("No results found.")
            continue

        for rank, result in enumerate(results, start=1):
            print(f"\n{rank}. {result['job_title']}")
            print(f"   Company: {result['company']}")
            print(f"   Location: {result['location']}")
            print(f"   Similarity: {result['similarity']}")
            print(f"   Section: {result['section']}")


if __name__ == "__main__":
    main()