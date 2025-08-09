def test_student_required_redirects_without_session(client):
    resp = client.get("/student/protected")
    # Redirect to home when no student_id in session
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")
