import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.main import app, create_database, get_connection
from backend.evaluation.evaluate_matching import load_profiles, load_jobs

def test_m3_flow():
    print("=" * 70)
    print("TESTING MILESTONE 3 BACKEND APIS END-TO-END")
    print("=" * 70)

    # 1. Initialize Database
    create_database()
    client = TestClient(app)

    # 2. Health check
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] GET /health returned 200 OK")

    # 3. Create or fetch test profile
    sample_profiles = load_profiles()
    sample_jobs = load_jobs()
    sample_student = sample_profiles[0] # Aarav Sharma

    profile_payload = {
        "full_name": sample_student["name"],
        "email": "aarav.sharma.test@example.com",
        "phone": "+91 9876543210",
        "location": "Bengaluru, India",
        "target_role": sample_student["target_role"],
        "linkedin_url": "https://linkedin.com/in/aaravsharma"
    }

    res = client.post("/profiles", json=profile_payload)
    assert res.status_code == 200, f"Create profile failed: {res.text}"
    profile_data = res.json()
    profile_id = profile_data["id"]
    print(f"[PASS] POST /profiles created profile ID {profile_id} ({profile_data['full_name']})")

    # 4. Mock a resume upload record in SQLite for this profile
    connection = get_connection()
    now_iso = "2026-09-22T12:00:00Z"
    extraction_payload = {
        "summary": "Experienced student in ML, Deep Learning and Computer Vision",
        "skills": sample_student["skills"],
        "education": [sample_student["education"]],
        "experience": [sample_student["experience"]],
        "projects": sample_student["projects"],
        "certifications": sample_student["qualifications"]
    }

    # Delete any existing test resumes for clean run
    connection.execute("DELETE FROM resumes WHERE profile_id = ?", (profile_id,))
    connection.execute(
        """
        INSERT INTO resumes (profile_id, filename, file_path, file_type, size_bytes, uploaded_at, extraction_json, extraction_method)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            profile_id,
            "aarav_sharma_resume.pdf",
            "/data/uploads/sample.pdf",
            ".pdf",
            10240,
            now_iso,
            json.dumps(extraction_payload),
            "gemini_llm"
        )
    )
    connection.commit()
    connection.close()
    print(f"[PASS] Injected verified candidate resume for profile ID {profile_id}")

    # 5. Test M3.1: Skill Gap API
    target_job = sample_jobs[0] # Python Intern (Techolution)
    skill_gap_payload = {
        "job_id": target_job["job_id"],
        "job_title": target_job["job_title"]
    }
    res = client.post(f"/profiles/{profile_id}/skill-gap", json=skill_gap_payload)
    assert res.status_code == 200, f"Skill gap failed: {res.text}"
    gap_data = res.json()
    print(f"[PASS] POST /profiles/{profile_id}/skill-gap returned 200 OK")
    print(f"    - Target Job: {gap_data.get('job_title')} at {gap_data.get('company')}")
    print(f"    - Skill Match %: {gap_data.get('skill_match_percentage')}%")
    print(f"    - Strong Matches: {len(gap_data.get('strong_matches', []))} items")
    print(f"    - Critical Gaps: {len(gap_data.get('critical_gaps', []))} items")
    print(f"    - Recommendations: {len(gap_data.get('recommendations', []))} items")
    assert "strong_matches" in gap_data
    assert "critical_gaps" in gap_data
    assert "recommendations" in gap_data

    # 6. Test M3.2: Customize Resume API
    res = client.post(f"/profiles/{profile_id}/customize-resume", json={"job_id": target_job["job_id"]})
    assert res.status_code == 200, f"Customize resume failed: {res.text}"
    resume_tailored = res.json()
    print(f"[PASS] POST /profiles/{profile_id}/customize-resume returned 200 OK")
    print(f"    - Tailored Summary: {resume_tailored.get('professional_summary')[:80]}...")
    print(f"    - Highlighted Skills: {resume_tailored.get('highlighted_skills')[:5]}")
    assert "professional_summary" in resume_tailored
    assert "highlighted_skills" in resume_tailored
    assert "projects" in resume_tailored

    # 7. Test M3.2: Cover Letter API
    res = client.post(f"/profiles/{profile_id}/cover-letter", json={"job_id": target_job["job_id"]})
    assert res.status_code == 200, f"Cover letter failed: {res.text}"
    cover_letter = res.json()
    print(f"[PASS] POST /profiles/{profile_id}/cover-letter returned 200 OK")
    print(f"    - Subject: {cover_letter.get('subject_line')}")
    print(f"    - Letter snippet: {cover_letter.get('full_letter')[:80]}...")
    assert "subject_line" in cover_letter
    assert "full_letter" in cover_letter

    # 8. Test M3.3: Interview Prep API
    res = client.post(f"/profiles/{profile_id}/interview-prep", json={"job_id": target_job["job_id"]})
    assert res.status_code == 200, f"Interview prep failed: {res.text}"
    prep = res.json()
    print(f"[PASS] POST /profiles/{profile_id}/interview-prep returned 200 OK")
    print(f"    - Tech Questions: {len(prep.get('technical_questions', []))}")
    print(f"    - Project Questions: {len(prep.get('project_questions', []))}")
    print(f"    - HR Questions: {len(prep.get('hr_questions', []))}")
    assert "technical_questions" in prep
    assert "project_questions" in prep
    assert "hr_questions" in prep

    # 9. Test M3.3: Mock Interview Simulator (Start + Answer)
    res = client.post(f"/profiles/{profile_id}/mock-interview/start", json={"job_id": target_job["job_id"]})
    assert res.status_code == 200, f"Mock interview start failed: {res.text}"
    mock_session = res.json()
    interview_id = mock_session["interview_id"]
    first_q = mock_session["current_question"]
    print(f"[PASS] POST /profiles/{profile_id}/mock-interview/start returned session ID {interview_id}")
    print(f"    - Question 1: \"{first_q['question']}\"")

    # Submit an answer to question 1
    answer_payload = {
        "interview_id": interview_id,
        "question_index": 0,
        "question_text": first_q["question"],
        "category": first_q.get("category", "Technical"),
        "user_answer": "I have used Python extensively for machine learning projects including TensorFlow and OpenCV. In my plant disease detection project, I built a convolutional neural network pipeline to classify leaf images with high accuracy."
    }
    res = client.post(f"/profiles/{profile_id}/mock-interview/answer", json=answer_payload)
    assert res.status_code == 200, f"Mock interview answer failed: {res.text}"
    answer_eval = res.json()
    print(f"[PASS] POST /profiles/{profile_id}/mock-interview/answer returned 200 OK")
    print(f"    - Overall Score: {answer_eval['evaluation'].get('overall_score')}/100")
    print(f"    - Technical Feedback: {answer_eval['evaluation'].get('technical_understanding', {}).get('feedback')}")
    print(f"    - Is Completed: {answer_eval.get('is_completed')}")

    # 10. Test M3.4: Career Assistant Chat API
    chat_payload = {
        "profile_id": profile_id,
        "job_id": target_job["job_id"],
        "message": "What skills should I learn first to improve my chances for this role?",
        "history": []
    }
    res = client.post("/career-assistant/chat", json=chat_payload)
    assert res.status_code == 200, f"Career assistant chat failed: {res.text}"
    chat_res = res.json()
    print(f"[PASS] POST /career-assistant/chat returned 200 OK")
    print(f"    - Assistant message snippet: {chat_res.get('message')[:100]}...")
    print(f"    - Context used: {chat_res.get('context_used')}")
    assert "message" in chat_res
    assert "context_used" in chat_res

    # 11. Test Chat History API
    res = client.get(f"/career-assistant/history/{profile_id}")
    assert res.status_code == 200
    history = res.json()
    print(f"[PASS] GET /career-assistant/history/{profile_id} returned {len(history.get('messages', []))} stored messages")

    print("\n" + "=" * 70)
    print("ALL M3 BACKEND APIS VERIFIED AND WORKING SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    test_m3_flow()
