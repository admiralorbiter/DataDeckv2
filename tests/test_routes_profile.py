from werkzeug.security import generate_password_hash

from models import User, db


def make_user(username: str, role: User.Role) -> User:
    u = User(
        username=username,
        email=f"{username}@example.com",
        password_hash=generate_password_hash("oldpw"),
        role=role,
    )
    db.session.add(u)
    db.session.commit()
    return u


def test_profile_password_change_flow(app, client):
    with app.app_context():
        make_user("peter", User.Role.TEACHER)
    client.post("/login", data={"username": "peter", "password": "oldpw"})

    resp = client.post(
        "/profile",
        data={
            "current_password": "oldpw",
            "new_password": "newpw",
            "confirm_password": "newpw",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
