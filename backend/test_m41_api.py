import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.main import app, create_database, get_connection

def test_m41_applications_flow():
    print("=" * 70)
    print("TESTING MILESTONE 4.1 APPLICATION TRACKER APIS END-TO-END")
    print("=" * 70)

    # 1. Initialize Database
    create_database()
    client = TestClient(app)

    # 2. Health check
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] GET /health returned 200 OK")

    # 3. Create or fetch test profile
    profile_payload = {
        "full_name": "Application Test User",
        "email": "app.test.user@example.com",
        "phone": "+91 9999999999",
        "location": "Bengaluru, India",
        "target_role": "Software Engineer Intern",
        "linkedin_url": "https://linkedin.com/in/apptestuser"
    }

    res = client.post("/profiles", json=profile_payload)
    assert res.status_code == 200, f"Create profile failed: {res.text}"
    profile_data = res.json()
    profile_id = profile_data["id"]
    print(f"[PASS] POST /profiles created profile ID {profile_id}")

    # Clean up existing test applications for clean test run
    connection = get_connection()
    connection.execute("DELETE FROM applications WHERE profile_id = ?", (profile_id,))
    connection.commit()
    connection.close()

    # 4. Test POST /profiles/{profile_id}/applications (Create application)
    app1_payload = {
        "job_id": "TEST_JOB_001",
        "company_name": "Google",
        "job_title": "Software Engineering Intern",
        "job_description": "Work on distributed cloud systems and AI algorithms.",
        "application_date": "2026-09-25",
        "deadline": "2026-10-15",
        "status": "Applied",
        "interview_date": "2026-10-05T10:00:00",
        "interview_status": "Scheduled",
        "notes": "Spoke with recruiter on LinkedIn. Coding round next.",
        "follow_up_date": "2026-10-01"
    }
    res = client.post(f"/profiles/{profile_id}/applications", json=app1_payload)
    assert res.status_code == 200, f"Create application 1 failed: {res.text}"
    app1 = res.json()
    app1_id = app1["id"]
    print(f"[PASS] POST /profiles/{profile_id}/applications created application ID {app1_id} ({app1['company_name']})")
    assert app1["company_name"] == "Google"
    assert app1["status"] == "Applied"
    assert app1["deadline_status"] == "upcoming"

    # 5. Test Duplicate Prevention (same job_id for same profile)
    res_dup = client.post(f"/profiles/{profile_id}/applications", json=app1_payload)
    assert res_dup.status_code == 400, f"Expected 400 on duplicate application, got {res_dup.status_code}"
    print("[PASS] Duplicate application correctly rejected with HTTP 400")

    # 6. Test Invalid Status Validation
    invalid_status_payload = {
        "company_name": "Test Co",
        "job_title": "Intern",
        "status": "NonExistentStatus"
    }
    res_inv = client.post(f"/profiles/{profile_id}/applications", json=invalid_status_payload)
    assert res_inv.status_code == 400, f"Expected 400 on invalid status, got {res_inv.status_code}"
    print("[PASS] Invalid status correctly rejected with HTTP 400")

    # 7. Create a second application (Manual entry, no job_id)
    app2_payload = {
        "company_name": "Microsoft",
        "job_title": "Data Science Intern",
        "job_description": "Build ML models for Azure cloud diagnostics.",
        "application_date": "2026-09-28",
        "deadline": "2026-09-29", # Overdue for test
        "status": "Planning to apply",
        "notes": "Need to tailor resume for PyTorch skills."
    }
    res = client.post(f"/profiles/{profile_id}/applications", json=app2_payload)
    assert res.status_code == 200, f"Create application 2 failed: {res.text}"
    app2 = res.json()
    app2_id = app2["id"]
    print(f"[PASS] POST /profiles/{profile_id}/applications created application ID {app2_id} ({app2['company_name']})")

    # 8. Test GET /profiles/{profile_id}/applications (List & Search & Filter)
    res = client.get(f"/profiles/{profile_id}/applications")
    assert res.status_code == 200, f"Get applications failed: {res.text}"
    apps_list = res.json()
    assert apps_list["count"] == 2
    print(f"[PASS] GET /profiles/{profile_id}/applications returned {apps_list['count']} applications")

    # Test Search
    res_search = client.get(f"/profiles/{profile_id}/applications?search=Google")
    assert res_search.json()["count"] == 1
    assert res_search.json()["applications"][0]["company_name"] == "Google"
    print("[PASS] GET applications with search filter succeeded")

    # Test Status Filter
    res_status = client.get(f"/profiles/{profile_id}/applications?status=Applied")
    assert res_status.json()["count"] == 1
    assert res_status.json()["applications"][0]["status"] == "Applied"
    print("[PASS] GET applications with status filter succeeded")

    # 9. Test GET /profiles/{profile_id}/applications/dashboard (Metrics)
    res_dash = client.get(f"/profiles/{profile_id}/applications/dashboard")
    assert res_dash.status_code == 200, f"Get dashboard failed: {res_dash.text}"
    dash_data = res_dash.json()
    metrics = dash_data["metrics"]
    print(f"[PASS] GET /profiles/{profile_id}/applications/dashboard returned metrics:")
    print(f"    - Total: {metrics['total_applications']}")
    print(f"    - Active: {metrics['active_applications']}")
    print(f"    - Upcoming Deadlines: {metrics['upcoming_deadlines']}")
    print(f"    - Interviews Scheduled: {metrics['interviews_scheduled']}")
    assert metrics["total_applications"] == 2
    assert metrics["active_applications"] == 2

    # 10. Test GET /profiles/{profile_id}/applications/{application_id} (Retrieve single)
    res_single = client.get(f"/profiles/{profile_id}/applications/{app1_id}")
    assert res_single.status_code == 200, f"Get single application failed: {res_single.text}"
    assert res_single.json()["id"] == app1_id
    print(f"[PASS] GET /profiles/{profile_id}/applications/{app1_id} retrieved successfully")

    # 11. Test PUT /profiles/{profile_id}/applications/{application_id} (Edit application & status change)
    update_payload = {
        "status": "Interview scheduled",
        "notes": "Updated notes: Technical interview confirmed for Oct 5!",
        "interview_date": "2026-10-05T14:00:00"
    }
    res_update = client.put(f"/profiles/{profile_id}/applications/{app1_id}", json=update_payload)
    assert res_update.status_code == 200, f"Update application failed: {res_update.text}"
    updated_app = res_update.json()
    assert updated_app["status"] == "Interview scheduled"
    assert "Technical interview confirmed" in updated_app["notes"]
    print(f"[PASS] PUT /profiles/{profile_id}/applications/{app1_id} updated status to '{updated_app['status']}'")

    # 12. Test DELETE /profiles/{profile_id}/applications/{application_id} (Delete application)
    res_del = client.delete(f"/profiles/{profile_id}/applications/{app2_id}")
    assert res_del.status_code == 200, f"Delete application failed: {res_del.text}"
    print(f"[PASS] DELETE /profiles/{profile_id}/applications/{app2_id} succeeded")

    # Verify count is now 1
    res_count = client.get(f"/profiles/{profile_id}/applications")
    assert res_count.json()["count"] == 1
    print("[PASS] Verified application count is 1 after deletion")

    # 13. Test 404 for invalid profile_id or application_id
    res_404_app = client.get(f"/profiles/{profile_id}/applications/999999")
    assert res_404_app.status_code == 404
    print("[PASS] Non-existent application ID returns 404 Not Found")

    res_404_prof = client.get("/profiles/999999/applications")
    assert res_404_prof.status_code == 404
    print("[PASS] Non-existent profile ID returns 404 Not Found")

    print("=" * 70)
    print("ALL MILESTONE 4.1 BACKEND API TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    test_m41_applications_flow()
