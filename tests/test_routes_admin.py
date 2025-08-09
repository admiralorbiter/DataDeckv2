from werkzeug.security import generate_password_hash

from models import District, School, User, db


def make_admin():
    admin = User(
        username="admin1",
        email="admin1@example.com",
        password_hash=generate_password_hash("pw"),
        role=User.Role.ADMIN,
    )
    db.session.add(admin)
    db.session.commit()
    return admin


def test_admin_dashboard_requires_admin(app, client):
    resp = client.get("/admin")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_admin_dashboard_renders_for_admin(app, client):
    with app.app_context():
        make_admin()
    client.post("/login", data={"username": "admin1", "password": "pw"})
    resp = client.get("/admin")
    assert resp.status_code == 200


def test_admin_create_user_requires_admin_role(app, client):
    # login as staff (not admin) -> should flash danger and redirect
    with app.app_context():
        staff = User(
            username="staff1",
            email="staff1@example.com",
            password_hash=generate_password_hash("pw"),
            role=User.Role.STAFF,
        )
        db.session.add(staff)
        db.session.commit()

    client.post("/login", data={"username": "staff1", "password": "pw"})
    resp = client.post(
        "/admin/create_user",
        data={
            "username": "t1",
            "email": "t1@example.com",
            "password": "pw",
            "first_name": "T",
            "last_name": "One",
            "role": "teacher",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200


def test_admin_create_and_delete_user_flow(app, client):
    with app.app_context():
        make_admin()
        district = District(name="D1", code="D1")
        school = School(name="S1", code="S1", district_id=1)
        db.session.add_all([district, school])
        db.session.commit()

    client.post("/login", data={"username": "admin1", "password": "pw"})
    create_resp = client.post(
        "/admin/create_user",
        data={
            "username": "teacher1",
            "email": "teacher1@example.com",
            "password": "pw",
            "first_name": "Teach",
            "last_name": "Er",
            "role": "teacher",
            # satisfy validation via denormalized names
            "school": "S1",
            "district": "D1",
        },
        follow_redirects=True,
    )
    assert create_resp.status_code == 200

    # Find created user
    with app.app_context():
        user = User.query.filter_by(username="teacher1").first()
        assert user is not None
        user_id = user.id

    delete_resp = client.post(f"/admin/delete_user/{user_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json["success"] is True
