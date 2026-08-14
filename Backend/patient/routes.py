from flask import Blueprint, redirect, render_template, request, session, url_for

import config
from auth.decorators import login_required, role_required
from patient.usecases import PatientUseCases
from system.usecases import SystemUseCases

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")

_usecases = PatientUseCases(config.DATA_DIR)
_system = SystemUseCases(config.DATA_DIR)


def _current_patient() -> str:
    return str(session.get("entity_id", ""))


def _dashboard_data(patient_id):
    return {
        "glicemia": _usecases.glicemia.find(patient_id=patient_id),
        "symptoms": _usecases.symptoms.find(patient_id=patient_id),
        "assunzioni": _usecases.assunzioni.find(patient_id=patient_id),
        "therapies": _usecases.list_therapies(patient_id),
        "concomitant": _usecases.concomitant.find(patient_id=patient_id),
    }


@patient_bp.route("/")
@login_required
@role_required("patient")
def dashboard():
    notifications = _usecases.view_notifications(_current_patient())
    return render_template(
        "patient/dashboard.html",
        current_username=session.get("username"),
        entity_id=_current_patient(),
        data=_dashboard_data(_current_patient()),
        notifications=notifications,
        reference_doctor=_usecases.view_reference_doctor(_current_patient()),
    )


@patient_bp.route("/glicemia", methods=["GET", "POST"])
@login_required
@role_required("patient")
def glicemia():
    patient_id = _current_patient()
    if request.method == "POST":
        _usecases.record_glicemia(
            patient_id,
            request.form["measured_on"],
            request.form.get("measured_at", ""),
            request.form["meal"],
            request.form["value"],
        )
        _system.alert_glucose(
            patient_id,
            request.form["value"],
            request.form["meal"],
            request.form["measured_on"],
        )
        return redirect(url_for("patient.glicemia"))
    readings = _usecases.glicemia.find(patient_id=patient_id)
    readings.reverse()
    return render_template(
        "patient/glicemia.html",
        current_username=session.get("username"),
        entity_id=patient_id,
        readings=readings,
    )


@patient_bp.route("/sintomi", methods=["GET", "POST"])
@login_required
@role_required("patient")
def symptoms():
    patient_id = _current_patient()
    if request.method == "POST":
        _usecases.add_symptom(
            patient_id,
            request.form["reported_on"],
            request.form["symptom"],
        )
        return redirect(url_for("patient.symptoms"))
    symptoms = _usecases.symptoms.find(patient_id=patient_id)
    symptoms.reverse()
    return render_template(
        "patient/symptoms.html",
        current_username=session.get("username"),
        entity_id=patient_id,
        symptoms=symptoms,
    )


@patient_bp.route("/assunzioni", methods=["GET", "POST"])
@login_required
@role_required("patient")
def assunzioni():
    patient_id = _current_patient()
    if request.method == "POST":
        _usecases.record_assunzione(
            patient_id,
            request.form["assumed_on"],
            request.form.get("assumed_at", ""),
            request.form["drug"],
            request.form["quantity"],
        )
        return redirect(url_for("patient.assunzioni"))
    assunzioni = _usecases.assunzioni.find(patient_id=patient_id)
    assunzioni.reverse()
    therapies = _usecases.list_therapies(patient_id)
    return render_template(
        "patient/assunzioni.html",
        current_username=session.get("username"),
        entity_id=patient_id,
        assunzioni=assunzioni,
        therapies=therapies,
    )


@patient_bp.route("/concomitanti", methods=["GET", "POST"])
@login_required
@role_required("patient")
def concomitant():
    patient_id = _current_patient()
    if request.method == "POST":
        _usecases.report_concomitant(
            patient_id,
            request.form["type"],
            request.form["description"],
            request.form.get("period", ""),
        )
        return redirect(url_for("patient.concomitant"))
    entries = _usecases.concomitant.find(patient_id=patient_id)
    entries.reverse()
    return render_template(
        "patient/concomitant.html",
        current_username=session.get("username"),
        entity_id=patient_id,
        entries=entries,
    )


@patient_bp.route("/contatto-medico", methods=["GET", "POST"])
@login_required
@role_required("patient")
def contact():
    patient_id = _current_patient()
    if request.method == "POST":
        _usecases.contact_doctor(patient_id, request.form["message"])
        return redirect(url_for("patient.contact"))
    contacts = _usecases.contacts.find(patient_id=patient_id)
    contacts.reverse()
    return render_template(
        "patient/contact.html",
        current_username=session.get("username"),
        entity_id=patient_id,
        contacts=contacts,
        reference_doctor=_usecases.view_reference_doctor(patient_id),
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
