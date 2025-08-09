from werkzeug.security import generate_password_hash

from models import User, db


def create_user(
    username: str, password: str, role: User.Role = User.Role.STUDENT
) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash=generate_password_hash(password),
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_login_success_redirects_home(app, client):
    with app.app_context():
        create_user("alice", "secret")

    resp = client.post("/login", data={"username": "alice", "password": "secret"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_login_invalid_credentials(app, client):
    with app.app_context():
        create_user("bob", "secret")

    resp = client.post("/login", data={"username": "bob", "password": "wrong"})
    # stays on login page (200)
    assert resp.status_code == 200


def test_logout_requires_login(client):
    resp = client.get("/logout")
    # Redirect to login because of @login_required
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_logout_after_login(app, client):
    with app.app_context():
        create_user("carol", "secret")
    client.post("/login", data={"username": "carol", "password": "secret"})
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")
