from fastapi.testclient import TestClient

import backend.main as main


def test_rag_startup():
    print("\nBEFORE CLIENT:")
    print("job_retriever =", main.job_retriever)
    print("matching_service =", main.matching_service)

    with TestClient(main.app) as client:

        print("\nINSIDE TEST CLIENT:")
        print("job_retriever =", main.job_retriever)
        print("matching_service =", main.matching_service)

        response = client.get("/health")

        print("\nHEALTH:")
        print(response.status_code)
        print(response.json())

        assert response.status_code == 200
        assert main.job_retriever is not None
        assert main.matching_service is not None