from flask import Blueprint, redirect, render_template, session, url_for

from auth.decorators import login_required, role_required

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")


@patient_bp.route("/")
@login_required
@role_required("patient")
def dashboard():
    return render_template(
        "patient/dashboard.html",
        current_username=session.get("username"),
        entity_id=session.get("entity_id"),
    )


@patient_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))