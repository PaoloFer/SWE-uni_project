from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from auth.decorators import login_required, role_required
from doctor.usecases import DoctorUseCases
from utils.csv_utils import CsvManager

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")

_usecases = DoctorUseCases("./data")


def _current_doctor() -> str:
    return str(session.get("entity_id", ""))


def _list_patients():
    manager = CsvManager("./data/patient.csv", delimiter=";")
    return manager.read()


@doctor_bp.route("/")
@login_required
@role_required("doctor")
def dashboard():
    patients = _list_patients()
    notifications = _usecases.view_notifications(_current_doctor())
    return render_template(
        "doctor/dashboard.html",
        patients=patients,
        notifications=notifications,
        current_doctor=_current_doctor(),
    )


@doctor_bp.route("/patients")
@login_required
@role_required("doctor")
def patients():
    patients = _list_patients()
    return render_template(
        "doctor/patients.html", patients=patients, current_doctor=_current_doctor()
    )


@doctor_bp.route("/patients/<int:patient_id>")
@login_required
@role_required("doctor")
def patient_detail(patient_id):
    data = _usecases.view_patient_data(patient_id)
    if data is None:
        return render_template(
            "doctor/patient_not_found.html",
            patient_id=patient_id,
            current_doctor=_current_doctor(),
        ), 404
    return render_template(
        "doctor/patient_detail.html",
        data=data,
        current_doctor=_current_doctor(),
    )


@doctor_bp.route("/patients/<int:patient_id>/trend")
@login_required
@role_required("doctor")
def patient_trend(patient_id):
    period = request.args.get("period", "week")
    trend = _usecases.view_glucose_trend(patient_id, period)
    return jsonify(trend)


@doctor_bp.route("/patients/<int:patient_id>/therapies", methods=["GET", "POST"])
@login_required
@role_required("doctor")
def therapy(patient_id):
    data = _usecases.view_patient_data(patient_id)
    if data is None:
        return render_template(
            "doctor/patient_not_found.html",
            patient_id=patient_id,
            current_doctor=_current_doctor(),
        ), 404

    if request.method == "POST":
        therapy_id = request.form.get("therapy_id")
        drug = request.form["drug"]
        daily_frequency = request.form["daily_frequency"]
        dose = request.form["dose"]
        indications = request.form.get("indications", "")

        if therapy_id:
            _usecases.modify_therapy(
                _current_doctor(), therapy_id, drug=drug, daily_frequency=daily_frequency,
                dose=dose, indications=indications,
            )
        else:
            _usecases.prescribe_therapy(
                _current_doctor(), patient_id, drug, daily_frequency, dose, indications,
            )
        return redirect(url_for("doctor.patient_detail", patient_id=patient_id))

    editing_id = request.args.get("edit")
    editing = None
    if editing_id:
        for therapy in data["therapies"]:
            if therapy["id"] == editing_id:
                editing = therapy
                break
    return render_template(
        "doctor/therapy_form.html",
        data=data,
        editing=editing,
        current_doctor=_current_doctor(),
    )


@doctor_bp.route("/patients/<int:patient_id>/clinical", methods=["GET", "POST"])
@login_required
@role_required("doctor")
def clinical_info(patient_id):
    data = _usecases.view_patient_data(patient_id)
    if data is None:
        return render_template(
            "doctor/patient_not_found.html",
            patient_id=patient_id,
            current_doctor=_current_doctor(),
        ), 404

    if request.method == "POST":
        _usecases.update_patient_info(
            _current_doctor(),
            patient_id,
            risk_factors=request.form.get("risk_factors", ""),
            past_pathologies=request.form.get("past_pathologies", ""),
            comorbidities=request.form.get("comorbidities", ""),
        )
        return redirect(url_for("doctor.patient_detail", patient_id=patient_id))

    info = _usecases.view_patient_info(patient_id)
    return render_template(
        "doctor/clinical_form.html",
        data=data,
        info=info,
        current_doctor=_current_doctor(),
    )


@doctor_bp.route("/notifications")
@login_required
@role_required("doctor")
def notifications():
    rows = _usecases.view_notifications(_current_doctor())
    return render_template(
        "doctor/notifications.html",
        notifications=rows,
        current_doctor=_current_doctor(),
    )


@doctor_bp.route("/notifications/<notification_id>/read")
@login_required
@role_required("doctor")
def mark_read(notification_id):
    _usecases.mark_notification_read(notification_id)
    return redirect(url_for("doctor.notifications"))