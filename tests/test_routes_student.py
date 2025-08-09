def test_student_required_redirects_without_session(client):
    """Test student_required decorator redirects when no student session."""
    resp = client.get("/student/protected")
    # Redirect to home when no student_id in session
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_student_login_endpoint_exists(client):
    """Test student login endpoint is accessible."""
    resp = client.get("/student/login")
    assert resp.status_code == 200
    assert b"Student Login" in resp.data or b"student" in resp.data.lower()


def test_student_logout_endpoint(client):
    """Test student logout endpoint."""
    with client.session_transaction() as sess:
        sess["student_id"] = 123

    resp = client.get("/student/logout")
    assert resp.status_code == 302

    # Verify student_id was removed from session
    with client.session_transaction() as sess:
        assert "student_id" not in sess
