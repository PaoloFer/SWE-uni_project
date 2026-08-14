from flask import Blueprint, redirect, render_template, session, url_for

from auth.decorators import login_required, role_required
from patient.usecases import PatientUseCases

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")

_usecases = PatientUseCases("./data")


def _current_patient() -> str:
    return str(session.get("entity_id", ""))


@patient_bp.route("/")
@login_required
@role_required("patient")
def dashboard():
    notifications = _usecases.view_notifications(_current_patient())
    return render_template(
        "patient/dashboard.html",
        current_username=session.get("username"),
        entity_id=_current_patient(),
        notifications=notifications,
    )


@patient_bp.route("/notifications")
@login_required
@role_required("patient")
def notifications():
    rows = _usecases.view_notifications(_current_patient())
    return render_template(
        "patient/notifications.html",
        notifications=rows,
        current_username=session.get("username"),
        entity_id=_current_patient(),
    )


@patient_bp.route("/notifications/<notification_id>/read")
@login_required
@role_required("patient")
def mark_read(notification_id):
    _usecases.mark_notification_read(notification_id, _current_patient())
    return redirect(url_for("patient.notifications"))


@patient_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))