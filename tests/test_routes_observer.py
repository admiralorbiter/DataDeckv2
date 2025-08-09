from werkzeug.security import generate_password_hash

from models import District, Observer, School, User, db


def make_observer(email: str, password: str, district: District) -> Observer:
    obs = Observer(
        username=email.split("@")[0],
        email=email,
        password_hash=generate_password_hash(password),
        role=User.Role.OBSERVER,
        district_id=district.id,
        is_active=True,
    )
    db.session.add(obs)
    db.session.commit()
    return obs


def make_school(name: str, district: District) -> School:
    s = School(name=name, code=f"{name[:3].upper()}1", district_id=district.id)
    db.session.add(s)
    db.session.commit()
    return s


def test_observer_login_success_redirects_dashboard(app, client):
    with app.app_context():
        d = District(name="D1", code="D1")
        db.session.add(d)
        db.session.commit()
        make_observer("obs@example.com", "pw", d)

    resp = client.post("/login", data={"username": "obs@example.com", "password": "pw"})
    assert resp.status_code == 302
    assert "/observer/dashboard" in resp.headers["Location"]


def test_observer_login_invalid_credentials(app, client):
    with app.app_context():
        d = District(name="D2", code="D2")
        db.session.add(d)
        db.session.commit()
        make_observer("bad@example.com", "pw", d)

    resp = client.post(
        "/login", data={"username": "bad@example.com", "password": "wrong"}
    )
    # stays on login page (200)
    assert resp.status_code == 200


def test_observer_required_redirects_without_session(client):
    resp = client.get("/observer/dashboard")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_observer_school_forbidden_other_district(app, client):
    with app.app_context():
        d1 = District(name="DA", code="DA")
        d2 = District(name="DB", code="DB")
        db.session.add_all([d1, d2])
        db.session.commit()
        make_observer("obs2@example.com", "pw", d1)
        school = make_school("SchoolB", d2)
        school_id = school.id

    # Login observer
    client.post("/login", data={"username": "obs2@example.com", "password": "pw"})
    # Try to access school from a different district
    resp = client.get(f"/observer/schools/{school_id}")
    assert resp.status_code == 403


def test_observer_school_lists_teachers(app, client):
    with app.app_context():
        d = District(name="DX", code="DX")
        db.session.add(d)
        db.session.commit()
        make_observer("obs3@example.com", "pw", d)
        school = make_school("SchoolX", d)
        school_id = school.id

        t = User(
            username="teachx",
            email="teachx@example.com",
            password_hash=generate_password_hash("pw"),
            role=User.Role.TEACHER,
            school_id=school.id,
            district_id=d.id,
            first_name="T",
            last_name="X",
        )
        db.session.add(t)
        db.session.commit()

    client.post("/login", data={"username": "obs3@example.com", "password": "pw"})
    resp = client.get(f"/observer/schools/{school_id}")
    assert resp.status_code == 200
    assert b"teachx@example.com" in resp.data
