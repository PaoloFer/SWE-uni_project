from flask import Blueprint, flash, redirect, render_template, request, session, url_for

import config
from auth.decorators import login_required, role_required
from patient.usecases import PatientUseCases
from system.usecases import SystemUseCases
from utils.csv_utils import CsvManager
from utils.validation import FormValidator

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")

_usecases = PatientUseCases(config.DATA_DIR)
_system = SystemUseCases(config.DATA_DIR)


def _current_patient() -> str:
    return str(session.get("entity_id", ""))


def _current_patient_name(patient_id: str) -> str:
    patients = CsvManager(f"{config.DATA_DIR}/patient.csv", delimiter=";")
    for p in patients.read():
        if p.get("id") == str(patient_id):
            return f"{p.get('name', '')} {p.get('surname', '')}".strip()
    return str(patient_id)


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
        patient_name=_current_patient_name(_current_patient()),
        data=_dashboard_data(_current_patient()),
        notifications=notifications,
        reference_doctor=_usecases.view_reference_doctor(_current_patient()),
    )


@patient_bp.route("/glicemia", methods=["GET", "POST"])
@login_required
@role_required("patient")
def glicemia():
    patient_id = _current_patient()
    readings = _usecases.glicemia.find(patient_id=patient_id)
    readings.reverse()

    form = {}
    errors = {}
    if request.method == "POST":
        v = FormValidator(request.form)
        measured_on = v.datef("measured_on", "Data", not_future=True)
        measured_at = v.timef("measured_at", "Ora")
        meal = v.choice("meal", ("pre", "post"), "Momento del pasto")
        value = v.numberf("value", "Valore (mg/dL)", minv=10, maxv=600)
        if not v.has_errors():
            _usecases.record_glicemia(patient_id, measured_on, measured_at, meal, value)
            _system.alert_glucose(patient_id, value, meal, measured_on)
            flash("Rilevazione di glicemia salvata correttamente.", "success")
            return redirect(url_for("patient.glicemia"))
        form = {k: request.form.get(k, "") for k in ("measured_on", "measured_at", "meal", "value")}
        errors = v.errors

    return render_template(
        "patient/glicemia.html",
        current_username=session.get("username"),
        entity_id=patient_id,
        readings=readings,
        form=form,
        errors=errors,
    )


@patient_bp.route("/sintomi", methods=["GET", "POST"])
@login_required
@role_required("patient")
def symptoms():
    patient_id = _current_patient()
    symptoms = _usecases.symptoms.find(patient_id=patient_id)
    symptoms.reverse()

    form = {}
    errors = {}
    if request.method == "POST":
        v = FormValidator(request.form)
        reported_on = v.datef("reported_on", "Data", not_future=True)
        symptom = v.required("symptom", "Sintomo", max_len=200)
        if not v.has_errors():
            _usecases.add_symptom(patient_id, reported_on, symptom)
            flash("Sintomo segnalato correttamente.", "success")
            return redirect(url_for("patient.symptoms"))
        form = {k: request.form.get(k, "") for k in ("reported_on", "symptom")}
        errors = v.errors

    return render_template(
        "patient/symptoms.html",
        current_username=session.get("username"),
        entity_id=patient_id,
        symptoms=symptoms,
        form=form,
        errors=errors,
    )


@patient_bp.route("/assunzioni", methods=["GET", "POST"])
@login_required
@role_required("patient")
def assunzioni():
    patient_id = _current_patient()
    assunzioni = _usecases.assunzioni.find(patient_id=patient_id)
    assunzioni.reverse()

    form = {}
    errors = {}
    if request.method == "POST":
        v = FormValidator(request.form)
        assumed_on = v.datef("assumed_on", "Data", not_future=True)
        assumed_at = v.timef("assumed_at", "Ora")
        drug = v.required("drug", "Farmaco", max_len=120)
        quantity = v.required("quantity", "Quantità", max_len=60)
        if not v.has_errors():
            _usecases.record_assunzione(patient_id, assumed_on, assumed_at, drug, quantity)
            flash("Assunzione registrata correttamente.", "success")
            return redirect(url_for("patient.assunzioni"))
        form = {k: request.form.get(k, "") for k in ("assumed_on", "assumed_at", "drug", "quantity")}
        errors = v.errors

    therapies = _usecases.list_therapies(patient_id)
    return render_template(
        "patient/assunzioni.html",
        current_username=session.get("username"),
        entity_id=patient_id,
        assunzioni=assunzioni,
        therapies=therapies,
        form=form,
        errors=errors,
    )


@patient_bp.route("/concomitanti", methods=["GET", "POST"])
@login_required
@role_required("patient")
def concomitant():
    patient_id = _current_patient()
    entries = _usecases.concomitant.find(patient_id=patient_id)
    entries.reverse()

    form = {}
    errors = {}
    if request.method == "POST":
        v = FormValidator(request.form)
        ctype = v.choice("type", ("sintomo", "patologia", "terapia"), "Tipo")
        description = v.required("description", "Descrizione", max_len=250)
        period = v.optional("period", "Periodo associato", max_len=60)
        if not v.has_errors():
            _usecases.report_concomitant(patient_id, ctype, description, period)
            flash("Segnalazione registrata correttamente.", "success")
            return redirect(url_for("patient.concomitant"))
        form = {k: request.form.get(k, "") for k in ("type", "description", "period")}
        errors = v.errors

    return render_template(
        "patient/concomitant.html",
        current_username=session.get("username"),
        entity_id=patient_id,
        entries=entries,
        form=form,
        errors=errors,
    )


@patient_bp.route("/contatto-medico", methods=["GET", "POST"])
@login_required
@role_required("patient")
def contact():
    patient_id = _current_patient()
    contacts = _usecases.contacts.find(patient_id=patient_id)
    contacts.reverse()

    form = {}
    errors = {}
    if request.method == "POST":
        v = FormValidator(request.form)
        message = v.required("message", "Messaggio", max_len=1000)
        if not v.has_errors():
            _usecases.contact_doctor(patient_id, message)
            flash("Messaggio inviato correttamente al medico.", "success")
            return redirect(url_for("patient.contact"))
        form = {k: request.form.get(k, "") for k in ("message",)}
        errors = v.errors

    return render_template(
        "patient/contact.html",
        current_username=session.get("username"),
        entity_id=patient_id,
        contacts=contacts,
        reference_doctor=_usecases.view_reference_doctor(patient_id),
        form=form,
        errors=errors,
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
