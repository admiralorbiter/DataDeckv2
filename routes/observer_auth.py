from flask import flash, redirect, render_template, session, url_for
from werkzeug.security import check_password_hash

from forms import ObserverLoginForm
from models import Observer

from .base import create_blueprint

bp = create_blueprint("observer_auth")


@bp.route("/observer/login", methods=["GET", "POST"])
def observer_login():
    form = ObserverLoginForm()
    if form.validate_on_submit():
        observer = Observer.query.filter_by(email=form.email.data).first()
        if observer and check_password_hash(observer.password_hash, form.password.data):
            session["observer_id"] = observer.id
            flash("Observer logged in.", "success")
            return redirect(url_for("main.observer_dashboard"))
        else:
            flash("Invalid email or password.", "danger")
    return render_template("observer_login.html", form=form)


@bp.route("/observer/logout", methods=["POST", "GET"])
def observer_logout():
    session.pop("observer_id", None)
    flash("Observer logged out.", "info")
    return redirect(url_for("main.index"))
