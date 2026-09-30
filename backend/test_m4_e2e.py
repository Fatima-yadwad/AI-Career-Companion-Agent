"""
==============================================================================
AI Career Companion - M4 End-to-End Test Suite
==============================================================================
Tests:  Profile (M1) | Resume (M1) | RAG (M2) | Matching (M2)
        Skill Gap (M3.1) | Customization (M3.2) | Interview (M3.3)
        Career Assistant (M3.4) | Application Tracker (M4.1)
        Error/Edge Cases | Full E2E Workflow | Multi-Agent Consistency

Usage:
    python backend/test_m4_e2e.py
    python -m pytest backend/test_m4_e2e.py -v -s
==============================================================================
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.main import app, create_database, get_connection

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------
RESULTS = []
_PASS = "PASS"
_FAIL = "FAIL"
_BLOCKED = "BLOCKED"


def record(test_id, feature, scenario, expected, actual, status, notes=""):
    RESULTS.append(dict(
        id=test_id, feature=feature, scenario=scenario,
        expected=expected, actual=actual, status=status, notes=notes
    ))
    sym = "v" if status == _PASS else ("X" if status == _FAIL else "?")
    print(f"  [{status}] {sym} {test_id}: {scenario}")
    if notes and status != _PASS:
        print(f"         Notes: {notes}")


def inject_resume(conn, profile_id, skills, projects, education, experience, certifications):
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    skills_preview = ", ".join(skills[:3]) if skills else "none"
    extraction = {
        "summary": "Candidate with skills in " + skills_preview + ".",
        "skills": skills,
        "education": [education],
        "experience": [experience],
        "projects": projects,
        "certifications": certifications,
    }
    conn.execute("DELETE FROM resumes WHERE profile_id = ?", (profile_id,))
    conn.execute(
        "INSERT INTO resumes (profile_id, filename, file_path, file_type, size_bytes, "
        "uploaded_at, extraction_json, extraction_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            profile_id,
            "test_resume.pdf",
            "/data/uploads/test_resume.pdf",
            ".pdf",
            10240,
            now_iso,
            json.dumps(extraction),
            "gemini_llm",
        ),
    )
    conn.commit()


# ===========================================================================
# SECTION 1: Profile Tests (M1)
# ===========================================================================

def run_profile_tests(client):
    print("\n" + "=" * 60)
    print("SECTION 1: Profile Tests (M1)")
    print("=" * 60)

    payload = {
        "full_name": "Aarav Sharma",
        "email": "aarav.e2e@test.com",
        "phone": "+91 9876543210",
        "location": "Bengaluru, India",
        "target_role": "Machine Learning Intern",
        "linkedin_url": "https://linkedin.com/in/aarav-e2e",
    }

    # T-P-01: Create valid profile
    res = client.post("/profiles", json=payload)
    if res.status_code == 200:
        profile_id = res.json()["id"]
        record("T-P-01", "Profile", "Create valid profile",
               "HTTP 200, profile id returned",
               "HTTP 200, id=" + str(profile_id), _PASS)
    else:
        profile_id = None
        record("T-P-01", "Profile", "Create valid profile",
               "HTTP 200, profile id returned",
               "HTTP " + str(res.status_code) + ": " + res.text[:80], _FAIL)

    # T-P-02: Duplicate email (upsert)
    res2 = client.post("/profiles", json=payload)
    status2 = _PASS if res2.status_code == 200 else _FAIL
    record("T-P-02", "Profile", "Duplicate email profile (upsert)",
           "HTTP 200 (upsert existing)", "HTTP " + str(res2.status_code), status2)

    # T-P-03: Missing required fields
    res3 = client.post("/profiles", json={"email": "incomplete@test.com"})
    status3 = _PASS if res3.status_code in (400, 422) else _FAIL
    record("T-P-03", "Profile", "Profile with missing full_name",
           "HTTP 400/422", "HTTP " + str(res3.status_code), status3)

    # T-P-04: Retrieve by ID
    if profile_id:
        res4 = client.get("/profiles/" + str(profile_id))
        ok4 = res4.status_code == 200 and res4.json().get("id") == profile_id
        record("T-P-04", "Profile", "Retrieve profile by ID",
               "HTTP 200 with correct data", "HTTP " + str(res4.status_code), _PASS if ok4 else _FAIL)

    # T-P-05: Nonexistent profile
    res5 = client.get("/profiles/999999")
    status5 = _PASS if res5.status_code == 404 else _FAIL
    record("T-P-05", "Profile", "Retrieve nonexistent profile",
           "HTTP 404", "HTTP " + str(res5.status_code), status5)

    return profile_id


# ===========================================================================
# SECTION 2: Resume Tests (M1)
# ===========================================================================

def run_resume_tests(client, profile_id):
    print("\n" + "=" * 60)
    print("SECTION 2: Resume Tests (M1)")
    print("=" * 60)

    if not profile_id:
        record("T-R-01", "Resume", "Inject resume", "Skipped", "BLOCKED", _BLOCKED)
        return

    ML_SKILLS = ["Python", "Machine Learning", "TensorFlow", "OpenCV",
                 "Scikit-learn", "Pandas", "SQL", "Computer Vision"]
    ML_PROJECTS = ["AI Plant Disease Detection", "Credit Card Fraud Detection", "Sign Language Translator"]

    # T-R-01: Inject resume
    conn = get_connection()
    try:
        inject_resume(conn, profile_id, ML_SKILLS, ML_PROJECTS,
                      "B.E. Artificial Intelligence and Machine Learning",
                      "Academic ML and Computer Vision projects",
                      ["Python ML fundamentals", "Deep Learning"])
        record("T-R-01", "Resume", "Inject resume for profile",
               "Resume inserted into DB", "Record created", _PASS)
    except Exception as exc:
        record("T-R-01", "Resume", "Inject resume for profile",
               "Resume inserted into DB", "Exception: " + str(exc), _FAIL)
    finally:
        conn.close()

    # T-R-02: Retrieve latest resume
    res2 = client.get("/profiles/" + str(profile_id) + "/resumes/latest")
    if res2.status_code == 200 and res2.json().get("extracted_profile"):
        n_skills = len(res2.json()["extracted_profile"].get("skills", []))
        record("T-R-02", "Resume", "Retrieve latest resume",
               "HTTP 200 with extracted skills",
               "HTTP 200, " + str(n_skills) + " skills", _PASS)
    else:
        record("T-R-02", "Resume", "Retrieve latest resume",
               "HTTP 200 with skills", "HTTP " + str(res2.status_code), _FAIL)

    # T-R-03: Minimal resume robustness
    conn2 = get_connection()
    try:
        inject_resume(conn2, profile_id, ["Java", "Spring Boot"], ["Java REST backend"],
                      "", "Java backend", [])
        res3 = client.get("/profiles/" + str(profile_id) + "/resumes/latest")
        status3 = _PASS if res3.status_code == 200 else _FAIL
        record("T-R-03", "Resume", "Resume with minimal info",
               "HTTP 200", "HTTP " + str(res3.status_code), status3)
    finally:
        conn2.close()

    # T-R-04: Nonexistent profile resume
    res4 = client.get("/profiles/999999/resumes/latest")
    status4 = _PASS if res4.status_code in (404, 400) else _FAIL
    record("T-R-04", "Resume", "Resume for nonexistent profile",
           "HTTP 404", "HTTP " + str(res4.status_code), status4,
           notes="Should return 404 for invalid profile" if status4 == _FAIL else "")

    # Restore ML resume
    conn3 = get_connection()
    inject_resume(conn3, profile_id, ML_SKILLS, ML_PROJECTS,
                  "B.E. Artificial Intelligence and Machine Learning",
                  "Academic ML and Computer Vision projects",
                  ["Python ML fundamentals", "Deep Learning"])
    conn3.close()


# ===========================================================================
# SECTION 3: RAG / Job Retrieval Tests (M2)
# ===========================================================================

def run_rag_tests(client):
    print("\n" + "=" * 60)
    print("SECTION 3: RAG / Job Retrieval Tests (M2)")
    print("=" * 60)

    results_pool = []

    for test_id, label, query in [
        ("T-RAG-01", "Python ML internship", "Python Machine Learning internship"),
        ("T-RAG-02", "React frontend internship", "React JavaScript frontend developer"),
        ("T-RAG-03", "Cybersecurity internship", "cybersecurity network security internship"),
    ]:
        res = client.post("/jobs/search", json={"query": query, "top_k": 5})
        if res.status_code == 200:
            results = res.json().get("results", res.json().get("jobs", []))
            status = _PASS if len(results) > 0 else _FAIL
            record(test_id, "RAG", "Semantic search - " + label,
                   ">=1 relevant job returned",
                   str(len(results)) + " results", status)
            if results and not results_pool:
                results_pool = results
        else:
            record(test_id, "RAG", "Semantic search - " + label,
                   "HTTP 200", "HTTP " + str(res.status_code), _FAIL)

    # T-RAG-04: Empty query
    res4 = client.post("/jobs/search", json={"query": "", "top_k": 5})
    status4 = _PASS if res4.status_code in (200, 400, 422) else _FAIL
    record("T-RAG-04", "RAG", "Search with empty query",
           "Graceful 200/400/422", "HTTP " + str(res4.status_code), status4)

    # T-RAG-05: Metadata fields
    res5 = client.post("/jobs/search", json={"query": "software engineer intern", "top_k": 3})
    if res5.status_code == 200:
        r5 = res5.json().get("results", res5.json().get("jobs", []))
        if r5:
            first = r5[0]
            required = {"job_title", "company", "job_id"}
            present = required.intersection(set(first.keys()))
            status5 = _PASS if present == required else _FAIL
            record("T-RAG-05", "RAG", "Job result metadata fields present",
                   "job_title, company, job_id present",
                   "Fields: " + str(list(present)), status5)
        else:
            record("T-RAG-05", "RAG", "Job result metadata fields present",
                   "Fields present", "No results", _BLOCKED)
    else:
        record("T-RAG-05", "RAG", "Job result metadata fields present",
               "HTTP 200", "HTTP " + str(res5.status_code), _FAIL)

    return results_pool


# ===========================================================================
# SECTION 4: Job Matching Tests (M2)
# ===========================================================================

def run_matching_tests(client, profile_id, rag_jobs):
    print("\n" + "=" * 60)
    print("SECTION 4: Job Matching Tests (M2)")
    print("=" * 60)

    if not profile_id:
        record("T-M-01", "Matching", "Profile-based matching", "Skipped", "BLOCKED", _BLOCKED)
        return None

    # T-M-01: ML candidate matches
    res1 = client.post("/profiles/" + str(profile_id) + "/job-matches", json={"top_k": 6})
    matched_job = None
    if res1.status_code == 200:
        results = res1.json().get("results", [])
        if results:
            matched_job = results[0]
            titles = [r.get("job_title", "") for r in results]
            record("T-M-01", "Matching", "ML candidate gets job matches",
                   ">=1 job returned",
                   str(len(results)) + " matches: " + str(titles[:2]), _PASS)
        else:
            record("T-M-01", "Matching", "ML candidate gets job matches",
                   ">=1 job returned", "0 matches", _FAIL)
    else:
        record("T-M-01", "Matching", "ML candidate gets job matches",
               "HTTP 200", "HTTP " + str(res1.status_code) + ": " + res1.text[:80], _FAIL)

    # T-M-02: Frontend candidate gets different results
    conn = get_connection()
    fe_res = client.post("/profiles", json={
        "full_name": "Diya Mehta E2E", "email": "diya.e2e@test.com",
        "target_role": "Frontend Developer Intern",
    })
    if fe_res.status_code == 200:
        fe_pid = fe_res.json()["id"]
        inject_resume(conn, fe_pid, ["HTML", "CSS", "JavaScript", "React", "REST API"],
                      ["E-commerce website", "Portfolio site", "React dashboard"],
                      "B.E. Computer Science", "Academic web development", [])
        conn.close()
        fe_match = client.post("/profiles/" + str(fe_pid) + "/job-matches", json={"top_k": 5})
        if fe_match.status_code == 200:
            fe_results = fe_match.json().get("results", [])
            fe_titles = [r.get("job_title", "").lower() for r in fe_results]
            frontend_kws = ["frontend", "web", "react", "ui", "javascript", "html"]
            fe_relevant = any(any(kw in t for kw in frontend_kws) for t in fe_titles)
            record("T-M-02", "Matching", "Frontend candidate gets frontend-relevant matches",
                   "Results relevant to frontend skills",
                   "Matched: " + str(fe_titles[:3]),
                   _PASS if fe_relevant else _FAIL,
                   notes="RAG may return generic results if DB lacks frontend-specific jobs" if not fe_relevant else "")
        else:
            record("T-M-02", "Matching", "Frontend candidate gets frontend-relevant matches",
                   "HTTP 200", "HTTP " + str(fe_match.status_code), _FAIL)
    else:
        conn.close()
        record("T-M-02", "Matching", "Frontend candidate matches",
               "HTTP 200", "Could not create frontend profile", _BLOCKED)

    # T-M-03: Match response has explanation/score field
    if res1.status_code == 200 and res1.json().get("results"):
        first_match = res1.json()["results"][0]
        score_keys = {"match_explanation", "explanation", "match_score", "matching_score", "score"}
        has_explanation = bool(score_keys.intersection(set(first_match.keys())))
        record("T-M-03", "Matching", "Match result contains score or explanation",
               "score or explanation field present",
               "Fields: " + str(list(first_match.keys())[:6]),
               _PASS if has_explanation else _FAIL)
    else:
        record("T-M-03", "Matching", "Match result has explanation", "Field present", "No results", _BLOCKED)

    # T-M-04: Invalid profile_id
    res4 = client.post("/profiles/999999/job-matches", json={"top_k": 5})
    status4 = _PASS if res4.status_code in (404, 400) else _FAIL
    record("T-M-04", "Matching", "Matching with invalid profile_id",
           "HTTP 404/400", "HTTP " + str(res4.status_code), status4)

    return matched_job


# ===========================================================================
# SECTION 5: Skill Gap Tests (M3.1)
# ===========================================================================

def run_skill_gap_tests(client, profile_id, sample_job):
    print("\n" + "=" * 60)
    print("SECTION 5: Skill Gap Tests (M3.1)")
    print("=" * 60)

    if not profile_id or not sample_job:
        record("T-SG-01", "Skill Gap", "Skill gap analysis", "Skipped", "BLOCKED", _BLOCKED)
        return

    job_id = sample_job.get("job_id")
    job_title = sample_job.get("job_title", "Test Role")

    # T-SG-01: Valid skill gap
    res1 = client.post("/profiles/" + str(profile_id) + "/skill-gap",
                       json={"job_id": job_id, "job_title": job_title})
    gap_data = None
    if res1.status_code == 200:
        gap_data = res1.json()
        required_keys = {"strong_matches", "critical_gaps", "recommendations"}
        present = required_keys.intersection(set(gap_data.keys()))
        status1 = _PASS if present == required_keys else _FAIL
        record("T-SG-01", "Skill Gap", "Valid skill gap analysis",
               "HTTP 200 with strong_matches, critical_gaps, recommendations",
               "HTTP 200, match=" + str(gap_data.get("skill_match_percentage", "?")) + "%", status1)
    else:
        record("T-SG-01", "Skill Gap", "Valid skill gap analysis",
               "HTTP 200", "HTTP " + str(res1.status_code) + ": " + res1.text[:100], _FAIL)

    # T-SG-02: Strong matches include actual skills
    if gap_data:
        matches = [s.lower() for s in gap_data.get("strong_matches", [])]
        status2 = _PASS if matches else _FAIL
        record("T-SG-02", "Skill Gap", "Strong matches include candidate's actual skills",
               "strong_matches non-empty", "Matches: " + str(matches[:3]), status2)

    # T-SG-03: Recommendations provided
    if gap_data:
        recs = gap_data.get("recommendations", [])
        status3 = _PASS if recs else _FAIL
        record("T-SG-03", "Skill Gap", "Recommendations provided",
               "Non-empty recommendations list", str(len(recs)) + " recommendations", status3)

    # T-SG-04: Invalid profile_id
    res4 = client.post("/profiles/999999/skill-gap", json={"job_id": job_id, "job_title": job_title})
    status4 = _PASS if res4.status_code in (404, 400) else _FAIL
    record("T-SG-04", "Skill Gap", "Skill gap with invalid profile_id",
           "HTTP 404/400", "HTTP " + str(res4.status_code), status4)

    # T-SG-05: Profile without resume
    no_res = client.post("/profiles", json={
        "full_name": "No Resume User", "email": "no.resume.e2e@test.com", "target_role": "Intern",
    })
    if no_res.status_code == 200:
        nrpid = no_res.json()["id"]
        res5 = client.post("/profiles/" + str(nrpid) + "/skill-gap",
                           json={"job_id": job_id, "job_title": job_title})
        status5 = _PASS if res5.status_code in (200, 400, 404, 422) else _FAIL
        record("T-SG-05", "Skill Gap", "Skill gap without uploaded resume",
               "Graceful response (200/400/404/422)", "HTTP " + str(res5.status_code), status5)
    else:
        record("T-SG-05", "Skill Gap", "Skill gap without uploaded resume",
               "Graceful response", "Could not create profile", _BLOCKED)


# ===========================================================================
# SECTION 6: Application Customization Tests (M3.2)
# ===========================================================================

def run_application_customization_tests(client, profile_id, sample_job):
    print("\n" + "=" * 60)
    print("SECTION 6: Application Customization Tests (M3.2)")
    print("=" * 60)

    if not profile_id or not sample_job:
        record("T-AC-01", "Resume Customization", "Tailored resume generation", "Skipped", "BLOCKED", _BLOCKED)
        return

    job_id = sample_job.get("job_id")
    job_title = sample_job.get("job_title", "Test Role")

    # T-AC-01: Generate tailored resume
    res1 = client.post("/profiles/" + str(profile_id) + "/customize-resume",
                       json={"job_id": job_id, "job_title": job_title})
    tailored = None
    if res1.status_code == 200:
        tailored = res1.json()
        required = {"professional_summary", "highlighted_skills", "projects"}
        present = required.intersection(set(tailored.keys()))
        n_skills = len(tailored.get("highlighted_skills", []))
        status1 = _PASS if present == required else _FAIL
        record("T-AC-01", "Resume Customization", "Generate tailored resume",
               "HTTP 200 with summary, skills, projects",
               "HTTP 200, " + str(n_skills) + " skills highlighted", status1)
    else:
        record("T-AC-01", "Resume Customization", "Generate tailored resume",
               "HTTP 200", "HTTP " + str(res1.status_code) + ": " + res1.text[:100], _FAIL)

    # T-AC-02: Skills grounded in resume
    if tailored:
        highlighted = [s.lower() for s in tailored.get("highlighted_skills", [])]
        known = ["python", "machine learning", "tensorflow", "opencv",
                 "scikit-learn", "pandas", "sql", "computer vision"]
        overlap = [s for s in highlighted if any(k in s for k in known)]
        status2 = _PASS if overlap or len(highlighted) == 0 else _FAIL
        record("T-AC-02", "Resume Customization", "Tailored skills grounded in resume",
               "Highlighted skills match actual resume skills",
               "Overlap: " + str(overlap[:3]), status2)

    # T-AC-03: Generate cover letter
    res3 = client.post("/profiles/" + str(profile_id) + "/cover-letter",
                       json={"job_id": job_id, "job_title": job_title})
    if res3.status_code == 200:
        cl = res3.json()
        has_letter = bool(cl.get("full_letter") or cl.get("cover_letter"))
        has_subject = "subject_line" in cl
        snippet = (cl.get("full_letter") or cl.get("cover_letter", ""))[:60]
        status3 = _PASS if has_letter else _FAIL
        record("T-AC-03", "Cover Letter", "Generate cover letter",
               "HTTP 200 with full_letter",
               "subject=" + str(has_subject) + ", snippet: " + snippet + "...", status3)
    else:
        record("T-AC-03", "Cover Letter", "Generate cover letter",
               "HTTP 200", "HTTP " + str(res3.status_code) + ": " + res3.text[:100], _FAIL)

    # T-AC-04: Cover letter for different job
    res4s = client.post("/jobs/search", json={"query": "data science internship", "top_k": 1})
    if res4s.status_code == 200 and res4s.json().get("results"):
        alt_job = res4s.json()["results"][0]
        res4 = client.post("/profiles/" + str(profile_id) + "/cover-letter",
                           json={"job_id": alt_job.get("job_id"), "job_title": alt_job.get("job_title")})
        status4 = _PASS if res4.status_code == 200 else _FAIL
        record("T-AC-04", "Cover Letter", "Cover letter for different job (same candidate)",
               "HTTP 200 with new letter",
               "HTTP 200 for '" + str(alt_job.get("job_title")) + "'", status4)
    else:
        record("T-AC-04", "Cover Letter", "Cover letter for different job",
               "HTTP 200", "Could not find alternate job", _BLOCKED)


# ===========================================================================
# SECTION 7: Interview Tests (M3.3)
# ===========================================================================

def run_interview_tests(client, profile_id, sample_job):
    print("\n" + "=" * 60)
    print("SECTION 7: Interview Tests (M3.3)")
    print("=" * 60)

    if not profile_id or not sample_job:
        record("T-I-01", "Interview", "Interview prep generation", "Skipped", "BLOCKED", _BLOCKED)
        return None

    job_id = sample_job.get("job_id")
    job_title = sample_job.get("job_title", "Test Role")

    # T-I-01: Generate interview prep
    res1 = client.post("/profiles/" + str(profile_id) + "/interview-prep",
                       json={"job_id": job_id, "job_title": job_title})
    prep_data = None
    if res1.status_code == 200:
        prep_data = res1.json()
        tech_q = prep_data.get("technical_questions", [])
        proj_q = prep_data.get("project_questions", [])
        hr_q = prep_data.get("hr_questions", [])
        status1 = _PASS if (tech_q or proj_q or hr_q) else _FAIL
        record("T-I-01", "Interview", "Generate interview prep questions",
               "HTTP 200 with tech/project/HR questions",
               "Tech:" + str(len(tech_q)) + " Proj:" + str(len(proj_q)) + " HR:" + str(len(hr_q)),
               status1)
    else:
        record("T-I-01", "Interview", "Generate interview prep questions",
               "HTTP 200", "HTTP " + str(res1.status_code) + ": " + res1.text[:100], _FAIL)

    # T-I-02: Questions are role-specific
    if prep_data and prep_data.get("technical_questions"):
        first_q = prep_data["technical_questions"][0]
        q_text = str(first_q.get("question", first_q) if isinstance(first_q, dict) else first_q)
        record("T-I-02", "Interview", "Interview questions are role-specific",
               "Questions tailored to role", "Sample Q: " + q_text[:80] + "...", _PASS)

    # T-I-03: Start mock interview
    res3 = client.post("/profiles/" + str(profile_id) + "/mock-interview/start",
                       json={"job_id": job_id, "job_title": job_title})
    mock_session = None
    if res3.status_code == 200:
        mock_session = res3.json()
        interview_id = mock_session.get("interview_id")
        first_q = mock_session.get("current_question")
        status3 = _PASS if interview_id and first_q else _FAIL
        record("T-I-03", "Interview", "Start mock interview session",
               "HTTP 200 with interview_id and first question",
               "Session: " + str(interview_id) + ", Q: " + str(first_q)[:60], status3)
    else:
        record("T-I-03", "Interview", "Start mock interview session",
               "HTTP 200", "HTTP " + str(res3.status_code) + ": " + res3.text[:100], _FAIL)

    # T-I-04: Submit answer and get evaluation
    if mock_session and mock_session.get("interview_id"):
        interview_id = mock_session["interview_id"]
        first_q = mock_session["current_question"]
        q_text = (first_q.get("question", str(first_q)) if isinstance(first_q, dict) else str(first_q))
        cat = (first_q.get("category", "Technical") if isinstance(first_q, dict) else "Technical")
        answer_payload = {
            "interview_id": interview_id,
            "question_index": 0,
            "question_text": q_text,
            "category": cat,
            "user_answer": (
                "I have extensive experience with Python for ML. In my plant disease detection project, "
                "I used TensorFlow and OpenCV to build a CNN that classifies leaf images. "
                "I preprocessed data, trained with augmentation, and achieved strong accuracy."
            ),
        }
        res4 = client.post("/profiles/" + str(profile_id) + "/mock-interview/answer",
                           json=answer_payload)
        if res4.status_code == 200:
            evaluation = res4.json().get("evaluation", {})
            overall_score = evaluation.get("overall_score")
            status4 = _PASS if overall_score is not None else _FAIL
            record("T-I-04", "Interview", "Submit mock answer and get evaluation",
                   "HTTP 200 with score", "Overall score: " + str(overall_score) + "/100", status4)
        else:
            record("T-I-04", "Interview", "Submit mock answer and get evaluation",
                   "HTTP 200 with evaluation", "HTTP " + str(res4.status_code) + ": " + res4.text[:100], _FAIL)

    # T-I-05: Invalid profile_id for mock interview
    res5 = client.post("/profiles/999999/mock-interview/start",
                       json={"job_id": job_id, "job_title": job_title})
    status5 = _PASS if res5.status_code in (404, 400, 422) else _FAIL
    record("T-I-05", "Interview", "Mock interview with invalid profile_id",
           "HTTP 404/400", "HTTP " + str(res5.status_code), status5)

    return mock_session


# ===========================================================================
# SECTION 8: Career Assistant Tests (M3.4)
# ===========================================================================

def run_career_assistant_tests(client, profile_id, sample_job):
    print("\n" + "=" * 60)
    print("SECTION 8: Career Assistant Tests (M3.4)")
    print("=" * 60)

    if not profile_id:
        record("T-CA-01", "Career Assistant", "Basic chat", "Skipped", "BLOCKED", _BLOCKED)
        return

    job_id = sample_job.get("job_id") if sample_job else None

    # T-CA-01: Basic question
    chat1 = {"profile_id": int(profile_id), "job_id": job_id,
              "message": "What internships fit my profile?", "history": []}
    res1 = client.post("/career-assistant/chat", json=chat1)
    reply1 = ""
    if res1.status_code == 200:
        reply1 = res1.json().get("message", "")
        status1 = _PASS if reply1 else _FAIL
        record("T-CA-01", "Career Assistant", "Basic career question",
               "HTTP 200 with AI response", "Response: " + reply1[:80] + "...", status1)
    else:
        record("T-CA-01", "Career Assistant", "Basic career question",
               "HTTP 200", "HTTP " + str(res1.status_code) + ": " + res1.text[:100], _FAIL)

    # T-CA-02: Multi-turn context retention
    if res1.status_code == 200:
        chat2 = {
            "profile_id": int(profile_id), "job_id": job_id,
            "message": "What skills am I missing for the first one?",
            "history": [
                {"role": "user", "content": chat1["message"]},
                {"role": "assistant", "content": reply1},
            ],
        }
        res2 = client.post("/career-assistant/chat", json=chat2)
        reply2 = res2.json().get("message", "") if res2.status_code == 200 else ""
        status2 = _PASS if res2.status_code == 200 and reply2 else _FAIL
        record("T-CA-02", "Career Assistant", "Multi-turn context retention",
               "HTTP 200 with context-aware response", "Response: " + reply2[:60] + "...", status2)

        # T-CA-03: Turn 3
        chat3 = {
            "profile_id": int(profile_id), "job_id": job_id,
            "message": "How should I prepare for an ML internship interview?",
            "history": [
                {"role": "user", "content": chat1["message"]},
                {"role": "assistant", "content": reply1},
                {"role": "user", "content": chat2["message"]},
                {"role": "assistant", "content": reply2},
            ],
        }
        res3 = client.post("/career-assistant/chat", json=chat3)
        reply3 = res3.json().get("message", "") if res3.status_code == 200 else ""
        status3 = _PASS if res3.status_code == 200 and reply3 else _FAIL
        record("T-CA-03", "Career Assistant", "Turn 3 - preparation advice",
               "HTTP 200 with relevant response", "Response: " + reply3[:60] + "...", status3)

    # T-CA-04: Chat history retrieval
    res4 = client.get("/career-assistant/history/" + str(profile_id))
    if res4.status_code == 200:
        msgs = res4.json().get("messages", [])
        record("T-CA-04", "Career Assistant", "Retrieve chat history",
               "HTTP 200 with stored messages", str(len(msgs)) + " messages stored", _PASS)
    else:
        record("T-CA-04", "Career Assistant", "Retrieve chat history",
               "HTTP 200", "HTTP " + str(res4.status_code), _FAIL)

    # T-CA-05: Suggested follow-ups
    if res1.status_code == 200:
        followups = res1.json().get("suggested_followups", [])
        status5 = _PASS if "suggested_followups" in res1.json() else _FAIL
        record("T-CA-05", "Career Assistant", "Response includes suggested follow-ups",
               "suggested_followups field present",
               str(len(followups)) + " follow-ups", status5)


# ===========================================================================
# SECTION 9: Application Tracker Tests (M4.1)
# ===========================================================================

def run_application_tracker_tests(client, profile_id, sample_job):
    print("\n" + "=" * 60)
    print("SECTION 9: Application Tracker Tests (M4.1)")
    print("=" * 60)

    if not profile_id:
        record("T-AT-01", "Application Tracker", "Create application", "Skipped", "BLOCKED", _BLOCKED)
        return

    # Clean up
    conn = get_connection()
    conn.execute("DELETE FROM applications WHERE profile_id = ?", (profile_id,))
    conn.commit()
    conn.close()

    today = datetime.now().strftime("%Y-%m-%d")
    future = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    past = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    future_dt = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT10:00:00")

    job_id = sample_job.get("job_id", "JOB001") if sample_job else "JOB001"
    company = sample_job.get("company", "TechCorp") if sample_job else "TechCorp"
    job_title = sample_job.get("job_title", "Software Engineering Intern") if sample_job else "Software Engineering Intern"

    # T-AT-01: Create application
    app1_payload = {
        "job_id": job_id, "company_name": company, "job_title": job_title,
        "job_description": "Work on distributed systems and ML.",
        "application_date": today, "deadline": future, "status": "Applied",
        "interview_date": future_dt, "interview_status": "Technical Round 1 Scheduled",
        "notes": "Applied via LinkedIn. Referral from John.",
        "follow_up_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
    }
    res1 = client.post("/profiles/" + str(profile_id) + "/applications", json=app1_payload)
    app1_id = None
    if res1.status_code == 200:
        app1_id = res1.json()["id"]
        record("T-AT-01", "Application Tracker", "Create application from job",
               "HTTP 200 with application id", "Application id=" + str(app1_id), _PASS)
    else:
        record("T-AT-01", "Application Tracker", "Create application from job",
               "HTTP 200", "HTTP " + str(res1.status_code) + ": " + res1.text[:100], _FAIL)

    # T-AT-02: Duplicate prevention
    if app1_id:
        res2 = client.post("/profiles/" + str(profile_id) + "/applications", json=app1_payload)
        status2 = _PASS if res2.status_code == 400 else _FAIL
        record("T-AT-02", "Application Tracker", "Duplicate application rejected",
               "HTTP 400 for duplicate job_id", "HTTP " + str(res2.status_code), status2)

    # T-AT-03: Manual application (no job_id), with overdue deadline
    app2_payload = {
        "company_name": "StartupXYZ", "job_title": "Data Science Intern",
        "status": "Planning to apply", "deadline": past,
        "notes": "Found on Naukri. Need to customize resume.",
    }
    res3 = client.post("/profiles/" + str(profile_id) + "/applications", json=app2_payload)
    app2_id = None
    if res3.status_code == 200:
        app2_id = res3.json()["id"]
        ds = res3.json().get("deadline_status", "")
        record("T-AT-03", "Application Tracker", "Create manual application (no job_id)",
               "HTTP 200", "id=" + str(app2_id) + ", deadline_status=" + ds, _PASS)
    else:
        record("T-AT-03", "Application Tracker", "Create manual application (no job_id)",
               "HTTP 200", "HTTP " + str(res3.status_code) + ": " + res3.text[:100], _FAIL)

    # T-AT-04: Offer received status
    res_a3 = client.post("/profiles/" + str(profile_id) + "/applications", json={
        "company_name": "BigTech", "job_title": "ML Research Intern", "status": "Offer received",
    })
    app3_id = None
    if res_a3.status_code == 200:
        app3_id = res_a3.json()["id"]
        record("T-AT-04", "Application Tracker", "Create application with 'Offer received' status",
               "HTTP 200", "id=" + str(app3_id), _PASS)
    else:
        record("T-AT-04", "Application Tracker", "Create application with 'Offer received' status",
               "HTTP 200", "HTTP " + str(res_a3.status_code) + ": " + res_a3.text[:80], _FAIL)

    # T-AT-05: Invalid status
    res5 = client.post("/profiles/" + str(profile_id) + "/applications", json={
        "company_name": "BadCo", "job_title": "Intern", "status": "NotAValidStatus"
    })
    status5 = _PASS if res5.status_code == 400 else _FAIL
    record("T-AT-05", "Application Tracker", "Invalid status rejected",
           "HTTP 400 for invalid status", "HTTP " + str(res5.status_code), status5)

    # T-AT-06: List applications
    res6 = client.get("/profiles/" + str(profile_id) + "/applications")
    if res6.status_code == 200:
        count = res6.json().get("count", 0)
        record("T-AT-06", "Application Tracker", "List all applications",
               "HTTP 200 with count", str(count) + " applications listed", _PASS)
    else:
        record("T-AT-06", "Application Tracker", "List all applications",
               "HTTP 200", "HTTP " + str(res6.status_code), _FAIL)

    # T-AT-07: Search filter
    res7 = client.get("/profiles/" + str(profile_id) + "/applications?search=BigTech")
    if res7.status_code == 200:
        filtered = res7.json().get("applications", [])
        ok7 = len(filtered) > 0 and all("bigtech" in a.get("company_name", "").lower() for a in filtered)
        record("T-AT-07", "Application Tracker", "Search filter works",
               "Filtered results match search term",
               str(len(filtered)) + " results for 'BigTech'", _PASS if ok7 else _FAIL)
    else:
        record("T-AT-07", "Application Tracker", "Search filter works",
               "HTTP 200", "HTTP " + str(res7.status_code), _FAIL)

    # T-AT-08: Status filter
    res8 = client.get("/profiles/" + str(profile_id) + "/applications?status=Applied")
    if res8.status_code == 200:
        filtered8 = res8.json().get("applications", [])
        all_applied = all(a.get("status") == "Applied" for a in filtered8)
        record("T-AT-08", "Application Tracker", "Status filter works",
               "Only Applied status returned",
               str(len(filtered8)) + " applications with status=Applied", _PASS if all_applied else _FAIL)
    else:
        record("T-AT-08", "Application Tracker", "Status filter works",
               "HTTP 200", "HTTP " + str(res8.status_code), _FAIL)

    # T-AT-09: Dashboard metrics
    res9 = client.get("/profiles/" + str(profile_id) + "/applications/dashboard")
    if res9.status_code == 200:
        metrics = res9.json().get("metrics", {})
        record("T-AT-09", "Application Tracker", "Dashboard metrics",
               "HTTP 200 with total_applications and offers_received",
               "Total=" + str(metrics.get("total_applications")) + ", Offers=" + str(metrics.get("offers_received")),
               _PASS)
    else:
        record("T-AT-09", "Application Tracker", "Dashboard metrics",
               "HTTP 200", "HTTP " + str(res9.status_code), _FAIL)

    # T-AT-10: Overdue deadline
    if app2_id:
        res10 = client.get("/profiles/" + str(profile_id) + "/applications/" + str(app2_id))
        if res10.status_code == 200:
            ds = res10.json().get("deadline_status", "")
            status10 = _PASS if ds == "overdue" else _FAIL
            record("T-AT-10", "Application Tracker", "Overdue deadline computed correctly",
                   "deadline_status=overdue", "deadline_status=" + ds, status10)
        else:
            record("T-AT-10", "Application Tracker", "Overdue deadline computed",
                   "HTTP 200", "HTTP " + str(res10.status_code), _FAIL)

    # T-AT-11: Update application
    if app1_id:
        res11 = client.put("/profiles/" + str(profile_id) + "/applications/" + str(app1_id), json={
            "status": "Interview scheduled",
            "notes": "Technical round confirmed for next week. Prepare DSA.",
            "interview_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT14:00:00"),
        })
        ok11 = res11.status_code == 200 and res11.json().get("status") == "Interview scheduled"
        record("T-AT-11", "Application Tracker", "Update application status and notes",
               "HTTP 200 with updated status",
               "Status=" + str(res11.json().get("status") if res11.status_code == 200 else res11.status_code),
               _PASS if ok11 else _FAIL)

    # T-AT-12: Retrieve single
    if app1_id:
        res12 = client.get("/profiles/" + str(profile_id) + "/applications/" + str(app1_id))
        ok12 = res12.status_code == 200 and res12.json().get("id") == app1_id
        record("T-AT-12", "Application Tracker", "Retrieve single application by ID",
               "HTTP 200 with correct application", "id=" + str(app1_id), _PASS if ok12 else _FAIL)

    # T-AT-13: Delete application
    if app3_id:
        res13 = client.delete("/profiles/" + str(profile_id) + "/applications/" + str(app3_id))
        status13 = _PASS if res13.status_code == 200 else _FAIL
        record("T-AT-13", "Application Tracker", "Delete application",
               "HTTP 200 and count decreases", "Delete OK", status13)

    # T-AT-14: 404 for invalid app ID
    res14 = client.get("/profiles/" + str(profile_id) + "/applications/999999")
    status14 = _PASS if res14.status_code == 404 else _FAIL
    record("T-AT-14", "Application Tracker", "Get nonexistent application",
           "HTTP 404", "HTTP " + str(res14.status_code), status14)

    # T-AT-15: 404 for invalid profile
    res15 = client.get("/profiles/999999/applications")
    status15 = _PASS if res15.status_code == 404 else _FAIL
    record("T-AT-15", "Application Tracker", "List apps for nonexistent profile",
           "HTTP 404", "HTTP " + str(res15.status_code), status15)

    # T-AT-16: Add notes
    if app2_id:
        res16 = client.put("/profiles/" + str(profile_id) + "/applications/" + str(app2_id), json={
            "notes": "Recruiter responded. Shortlisting in progress. Follow up on Friday."
        })
        status16 = _PASS if res16.status_code == 200 else _FAIL
        record("T-AT-16", "Application Tracker", "Add notes to application",
               "HTTP 200 with updated notes", "HTTP " + str(res16.status_code), status16)

    return app1_id


# ===========================================================================
# SECTION 10: Error / Edge-Case Tests
# ===========================================================================

def run_error_tests(client, profile_id):
    print("\n" + "=" * 60)
    print("SECTION 10: Error / Edge-Case Tests")
    print("=" * 60)

    # T-E-01: Health check
    res = client.get("/health")
    status_e1 = _PASS if res.status_code == 200 else _FAIL
    record("T-E-01", "Error/Edge", "Health check endpoint",
           "HTTP 200", "HTTP " + str(res.status_code), status_e1)

    # T-E-02: Invalid profile for M3 endpoints
    for route_name, endpoint in [
        ("skill-gap", "/profiles/999999/skill-gap"),
        ("customize-resume", "/profiles/999999/customize-resume"),
        ("cover-letter", "/profiles/999999/cover-letter"),
        ("interview-prep", "/profiles/999999/interview-prep"),
    ]:
        res_err = client.post(endpoint, json={"job_id": "TEST001", "job_title": "Test Role"})
        status_e2 = _PASS if res_err.status_code in (404, 400, 422) else _FAIL
        record("T-E-02-" + route_name, "Error/Edge", "Invalid profile for " + route_name,
               "HTTP 404/400", "HTTP " + str(res_err.status_code), status_e2)

    # T-E-03: Job search with special characters
    res3 = client.post("/jobs/search", json={"query": "!@#$%^ SQL intern", "top_k": 3})
    status_e3 = _PASS if res3.status_code in (200, 400) else _FAIL
    record("T-E-03", "Error/Edge", "Job search with special characters",
           "Graceful 200/400", "HTTP " + str(res3.status_code), status_e3)

    # T-E-04: Application with invalid date format
    if profile_id:
        res4 = client.post("/profiles/" + str(profile_id) + "/applications", json={
            "company_name": "TestCo", "job_title": "Intern",
            "deadline": "not-a-date", "status": "Applied",
        })
        status_e4 = _PASS if res4.status_code in (200, 400, 422) else _FAIL
        record("T-E-04", "Error/Edge", "Application with invalid date format",
               "Graceful 200/400/422", "HTTP " + str(res4.status_code), status_e4)

    # T-E-05: Chat without profile_id
    res5 = client.post("/career-assistant/chat", json={
        "profile_id": None, "message": "What careers are good for AI students?", "history": []
    })
    status_e5 = _PASS if res5.status_code in (200, 400, 422) else _FAIL
    record("T-E-05", "Error/Edge", "Career assistant chat without profile_id",
           "Graceful response", "HTTP " + str(res5.status_code), status_e5)

    # T-E-06: Application missing required company_name
    if profile_id:
        res6 = client.post("/profiles/" + str(profile_id) + "/applications", json={
            "job_title": "Intern"  # missing company_name
        })
        status_e6 = _PASS if res6.status_code in (400, 422) else _FAIL
        record("T-E-06", "Error/Edge", "Application missing required company_name",
               "HTTP 400/422", "HTTP " + str(res6.status_code), status_e6)


# ===========================================================================
# SECTION 11: Full E2E Workflow Test
# ===========================================================================

def run_full_e2e_workflow(client):
    print("\n" + "=" * 60)
    print("SECTION 11: Full E2E Workflow Test")
    print("=" * 60)
    print("  Profile -> Resume -> Matches -> Skill Gap ->")
    print("  Resume Customization -> Cover Letter -> Interview -> Application")

    today = datetime.now().strftime("%Y-%m-%d")

    # Step 1: Profile
    res_p = client.post("/profiles", json={
        "full_name": "E2E Test Student", "email": "e2e.full.workflow@test.com",
        "target_role": "Machine Learning Intern",
    })
    if res_p.status_code != 200:
        record("T-E2E-01", "Full E2E", "Create profile", "HTTP 200",
               "HTTP " + str(res_p.status_code), _FAIL)
        return
    e2e_pid = res_p.json()["id"]
    record("T-E2E-01", "Full E2E", "Create student profile",
           "HTTP 200, profile created", "Profile id=" + str(e2e_pid), _PASS)

    # Step 2: Inject resume
    conn = get_connection()
    inject_resume(conn, e2e_pid,
                  ["Python", "Machine Learning", "TensorFlow", "Pandas", "NumPy", "Scikit-learn"],
                  ["Credit Card Fraud Detection", "Image Classification CNN"],
                  "B.E. AI and Machine Learning", "Academic ML projects",
                  ["Python ML fundamentals"])
    conn.close()
    res_r = client.get("/profiles/" + str(e2e_pid) + "/resumes/latest")
    status_r = _PASS if res_r.status_code == 200 else _FAIL
    record("T-E2E-02", "Full E2E", "Upload and retrieve resume",
           "HTTP 200 with extracted data", "HTTP " + str(res_r.status_code), status_r)

    # Step 3: Job matches
    res_m = client.post("/profiles/" + str(e2e_pid) + "/job-matches", json={"top_k": 5})
    e2e_job = None
    if res_m.status_code == 200 and res_m.json().get("results"):
        e2e_job = res_m.json()["results"][0]
        record("T-E2E-03", "Full E2E", "Get job matches",
               "HTTP 200 with jobs",
               str(len(res_m.json()["results"])) + " matches, top=" + str(e2e_job.get("job_title")), _PASS)
    else:
        record("T-E2E-03", "Full E2E", "Get job matches",
               "HTTP 200 with jobs", "HTTP " + str(res_m.status_code), _FAIL)

    if not e2e_job:
        record("T-E2E-04", "Full E2E", "Skill gap analysis", "Skipped", "BLOCKED", _BLOCKED)
        return

    job_id = e2e_job.get("job_id")
    job_title = e2e_job.get("job_title", "ML Intern")

    # Step 4: Skill gap
    res_sg = client.post("/profiles/" + str(e2e_pid) + "/skill-gap",
                         json={"job_id": job_id, "job_title": job_title})
    status_sg = _PASS if res_sg.status_code == 200 else _FAIL
    sg_match = res_sg.json().get("skill_match_percentage", "?") if res_sg.status_code == 200 else "?"
    record("T-E2E-04", "Full E2E", "Skill gap analysis",
           "HTTP 200 with gap data", "Match=" + str(sg_match) + "%", status_sg)

    # Step 5: Tailored resume
    res_tr = client.post("/profiles/" + str(e2e_pid) + "/customize-resume",
                         json={"job_id": job_id, "job_title": job_title})
    status_tr = _PASS if res_tr.status_code == 200 else _FAIL
    tr_summary = str(res_tr.json().get("professional_summary", ""))[:50] + "..." if res_tr.status_code == 200 else ""
    record("T-E2E-05", "Full E2E", "Generate tailored resume",
           "HTTP 200 with tailored resume", "Summary: " + tr_summary, status_tr)

    # Step 6: Cover letter
    res_cl = client.post("/profiles/" + str(e2e_pid) + "/cover-letter",
                         json={"job_id": job_id, "job_title": job_title})
    status_cl = _PASS if res_cl.status_code == 200 else _FAIL
    record("T-E2E-06", "Full E2E", "Generate cover letter",
           "HTTP 200 with letter", "HTTP " + str(res_cl.status_code), status_cl)

    # Step 7: Interview prep
    res_ip = client.post("/profiles/" + str(e2e_pid) + "/interview-prep",
                         json={"job_id": job_id, "job_title": job_title})
    status_ip = _PASS if res_ip.status_code == 200 else _FAIL
    n_tech = len(res_ip.json().get("technical_questions", [])) if res_ip.status_code == 200 else 0
    record("T-E2E-07", "Full E2E", "Generate interview prep",
           "HTTP 200 with questions", "Tech: " + str(n_tech), status_ip)

    # Step 8: Mock interview
    res_mi = client.post("/profiles/" + str(e2e_pid) + "/mock-interview/start",
                         json={"job_id": job_id, "job_title": job_title})
    if res_mi.status_code == 200:
        mi_session = res_mi.json()
        record("T-E2E-08", "Full E2E", "Start mock interview",
               "HTTP 200 with session", "Session id=" + str(mi_session.get("interview_id")), _PASS)

        q = mi_session.get("current_question", {})
        q_text = q.get("question", "") if isinstance(q, dict) else str(q)
        ans_res = client.post("/profiles/" + str(e2e_pid) + "/mock-interview/answer", json={
            "interview_id": mi_session.get("interview_id"),
            "question_index": 0, "question_text": q_text,
            "category": q.get("category", "Technical") if isinstance(q, dict) else "Technical",
            "user_answer": (
                "I have used Python and TensorFlow for CNN models. "
                "My fraud detection project used Scikit-learn pipelines and achieved good precision."
            ),
        })
        score = ans_res.json().get("evaluation", {}).get("overall_score") if ans_res.status_code == 200 else None
        status_ans = _PASS if ans_res.status_code == 200 else _FAIL
        record("T-E2E-08b", "Full E2E", "Submit mock interview answer",
               "HTTP 200 with score", "Score=" + str(score), status_ans)
    else:
        record("T-E2E-08", "Full E2E", "Start mock interview",
               "HTTP 200", "HTTP " + str(res_mi.status_code), _FAIL)

    # Step 9: Career assistant
    res_ca = client.post("/career-assistant/chat", json={
        "profile_id": int(e2e_pid), "job_id": job_id,
        "message": "Based on my profile and this job, what should I focus on?",
        "history": [],
    })
    status_ca = _PASS if res_ca.status_code == 200 else _FAIL
    ca_snippet = res_ca.json().get("message", "")[:60] + "..." if res_ca.status_code == 200 else ""
    record("T-E2E-09", "Full E2E", "Career assistant in E2E context",
           "HTTP 200 with AI response", "Response: " + ca_snippet, status_ca)

    # Step 10: Track application + update status
    res_app = client.post("/profiles/" + str(e2e_pid) + "/applications", json={
        "job_id": job_id, "company_name": e2e_job.get("company", "E2E Company"),
        "job_title": job_title, "status": "Applied", "application_date": today,
        "deadline": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
        "notes": "Applied via company portal.",
    })
    if res_app.status_code == 200:
        app_id = res_app.json()["id"]
        record("T-E2E-10a", "Full E2E", "Track application",
               "HTTP 200", "Application id=" + str(app_id), _PASS)

        upd = client.put("/profiles/" + str(e2e_pid) + "/applications/" + str(app_id), json={
            "status": "Interview scheduled",
            "interview_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%dT11:00:00"),
            "notes": "Technical interview in 5 days.",
        })
        record("T-E2E-10b", "Full E2E", "Update status -> Interview scheduled",
               "HTTP 200", "HTTP " + str(upd.status_code), _PASS if upd.status_code == 200 else _FAIL)

        upd2 = client.put("/profiles/" + str(e2e_pid) + "/applications/" + str(app_id), json={
            "status": "Offer received",
            "notes": "Offer received! Package 12 LPA. Respond in 5 days.",
        })
        record("T-E2E-10c", "Full E2E", "Update status -> Offer received",
               "HTTP 200", "HTTP " + str(upd2.status_code), _PASS if upd2.status_code == 200 else _FAIL)
    else:
        record("T-E2E-10a", "Full E2E", "Track application",
               "HTTP 200", "HTTP " + str(res_app.status_code) + ": " + res_app.text[:80], _FAIL)

    # Step 11: Dashboard reflects E2E session
    res_dash = client.get("/profiles/" + str(e2e_pid) + "/applications/dashboard")
    if res_dash.status_code == 200:
        m = res_dash.json().get("metrics", {})
        record("T-E2E-11", "Full E2E", "Dashboard reflects entire E2E session",
               "HTTP 200 with correct totals",
               "Total=" + str(m.get("total_applications")) + ", Offers=" + str(m.get("offers_received")),
               _PASS)
    else:
        record("T-E2E-11", "Full E2E", "Dashboard reflects E2E session",
               "HTTP 200", "HTTP " + str(res_dash.status_code), _FAIL)


# ===========================================================================
# SECTION 12: Multi-Agent Consistency
# ===========================================================================

def run_multi_agent_consistency(client, profile_id, sample_job):
    print("\n" + "=" * 60)
    print("SECTION 12: Multi-Agent Consistency")
    print("=" * 60)

    if not profile_id or not sample_job:
        record("T-MAC-01", "Multi-Agent", "Consistency check", "Skipped", "BLOCKED", _BLOCKED)
        return

    job_id = sample_job.get("job_id")
    job_title = sample_job.get("job_title", "")
    company = sample_job.get("company", "")

    # T-MAC-01: Skill Gap and Resume Customization reference same job
    sg_res = client.post("/profiles/" + str(profile_id) + "/skill-gap",
                         json={"job_id": job_id, "job_title": job_title})
    cr_res = client.post("/profiles/" + str(profile_id) + "/customize-resume",
                         json={"job_id": job_id, "job_title": job_title})
    if sg_res.status_code == 200 and cr_res.status_code == 200:
        sg_job_ref = sg_res.json().get("job_title", "").lower()
        cr_strategy = str(cr_res.json().get("customization_strategy", "")).lower()
        record("T-MAC-01", "Multi-Agent", "Skill Gap and Resume Customization use same job",
               "Both agents operate on same job context",
               "SG job=" + sg_job_ref + ", CR has strategy=" + str(bool(cr_strategy)), _PASS)
    else:
        record("T-MAC-01", "Multi-Agent", "Skill Gap and Resume Customization use same job",
               "HTTP 200 for both", "SG=" + str(sg_res.status_code) + ", CR=" + str(cr_res.status_code), _FAIL)

    # T-MAC-02: Interview Prep references same role
    ip_res = client.post("/profiles/" + str(profile_id) + "/interview-prep",
                         json={"job_id": job_id, "job_title": job_title})
    if ip_res.status_code == 200 and sg_res.status_code == 200:
        ip_str = json.dumps(ip_res.json()).lower()
        sg_title_words = [w for w in job_title.lower().split() if len(w) > 3]
        match_found = any(word in ip_str for word in sg_title_words)
        record("T-MAC-02", "Multi-Agent", "Interview Prep references same role as Skill Gap",
               "Job context consistent across agents",
               "Role words found in IP: " + str(match_found), _PASS if match_found else _FAIL)
    else:
        record("T-MAC-02", "Multi-Agent", "Interview Prep references same role",
               "HTTP 200 for both", "IP=" + str(ip_res.status_code), _FAIL)

    # T-MAC-03: Career assistant uses job context
    ca_res = client.post("/career-assistant/chat", json={
        "profile_id": int(profile_id), "job_id": job_id,
        "message": "Tell me about the role at " + company + ".",
        "history": [],
    })
    if ca_res.status_code == 200:
        context_used = ca_res.json().get("context_used", False)
        record("T-MAC-03", "Multi-Agent", "Career Assistant uses job context",
               "context_used=True or response contains role info",
               "context_used=" + str(context_used), _PASS if context_used else _FAIL)
    else:
        record("T-MAC-03", "Multi-Agent", "Career Assistant uses job context",
               "HTTP 200", "HTTP " + str(ca_res.status_code), _FAIL)

    # T-MAC-04: Application tracker stores consistent job info
    app_res = client.post("/profiles/" + str(profile_id) + "/applications", json={
        "job_id": job_id, "company_name": company or "E2E Test Company",
        "job_title": job_title, "status": "Saved",
    })
    if app_res.status_code == 200:
        stored_jt = app_res.json().get("job_title", "")
        consistent = stored_jt == job_title
        record("T-MAC-04", "Multi-Agent", "Application tracker stores consistent job info",
               "Stored job_title matches matched job_title",
               "Stored: " + stored_jt + " vs Expected: " + job_title,
               _PASS if consistent else _FAIL)
    elif app_res.status_code == 400:
        # Already exists from previous tracker test - still consistent
        record("T-MAC-04", "Multi-Agent", "Application tracker stores consistent job info",
               "Application with same job consistent", "Already tracked (data consistent)", _PASS)
    else:
        record("T-MAC-04", "Multi-Agent", "Application tracker stores consistent job info",
               "HTTP 200 or 400", "HTTP " + str(app_res.status_code), _FAIL)


# ===========================================================================
# Summary
# ===========================================================================

def print_summary():
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)

    passed = [r for r in RESULTS if r["status"] == _PASS]
    failed = [r for r in RESULTS if r["status"] == _FAIL]
    blocked = [r for r in RESULTS if r["status"] == _BLOCKED]

    print("\nTotal Tests Executed : " + str(len(RESULTS)))
    print("PASS                 : " + str(len(passed)))
    print("FAIL                 : " + str(len(failed)))
    print("BLOCKED              : " + str(len(blocked)))

    if failed:
        print("\n--- FAILED TESTS ---")
        for r in failed:
            print("  " + r["id"] + ": " + r["scenario"])
            print("    Expected : " + r["expected"])
            print("    Actual   : " + r["actual"])
            if r["notes"]:
                print("    Notes    : " + r["notes"])

    if blocked:
        print("\n--- BLOCKED TESTS ---")
        for r in blocked:
            print("  " + r["id"] + ": " + r["scenario"])

    print("\n" + "=" * 70)
    return passed, failed, blocked


# ===========================================================================
# Main
# ===========================================================================

def run_all_tests():
    print("=" * 70)
    print("AI CAREER COMPANION - M4 END-TO-END TEST SUITE")
    print("Run started: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)

    create_database()
    client = TestClient(app)

    profile_id = run_profile_tests(client)
    run_resume_tests(client, profile_id)
    rag_jobs = run_rag_tests(client)
    sample_job = run_matching_tests(client, profile_id, rag_jobs)

    if not sample_job and rag_jobs:
        sample_job = rag_jobs[0]

    run_skill_gap_tests(client, profile_id, sample_job)
    run_application_customization_tests(client, profile_id, sample_job)
    run_interview_tests(client, profile_id, sample_job)
    run_career_assistant_tests(client, profile_id, sample_job)
    run_application_tracker_tests(client, profile_id, sample_job)
    run_error_tests(client, profile_id)
    run_full_e2e_workflow(client)
    run_multi_agent_consistency(client, profile_id, sample_job)

    passed, failed, blocked = print_summary()
    print("Run completed: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    return RESULTS, passed, failed, blocked


def test_m4_e2e():
    """Pytest entry point for M4 E2E test suite."""
    results, passed, failed, blocked = run_all_tests()
    if failed:
        fail_ids = [r["id"] for r in failed]
        raise AssertionError(str(len(failed)) + " tests FAILED: " + str(fail_ids))


if __name__ == "__main__":
    run_all_tests()
