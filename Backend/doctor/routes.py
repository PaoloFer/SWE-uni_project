from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

import config
from auth.decorators import login_required, role_required
from doctor.usecases import DoctorUseCases
from system.usecases import SystemUseCases
from utils.csv_utils import CsvManager
from utils.validation import FormValidator

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")

_usecases = DoctorUseCases(config.DATA_DIR)
_system = SystemUseCases(config.DATA_DIR)


def _current_doctor() -> str:
    return str(session.get("entity_id", ""))


def _is_assigned(patient_id) -> bool:
    associations = CsvManager(f"{config.DATA_DIR}/associations.csv", delimiter=";")
    return any(
        a["patient_id"] == str(patient_id) and a["doctor_id"] == _current_doctor()
        for a in associations.read()
    )


def _list_patients(doctor_id: str = ""):
    manager = CsvManager(f"{config.DATA_DIR}/patient.csv", delimiter=";")
    patients = manager.read()
    associations = CsvManager(f"{config.DATA_DIR}/associations.csv", delimiter=";")
    doctors = CsvManager(f"{config.DATA_DIR}/doctors.csv", delimiter=";")
    assoc_map = {a["patient_id"]: a["doctor_id"] for a in associations.read()}
    doctor_map = {
        d["id"]: f"{d['name']} {d['surname']}"
        for d in doctors.read()
    }
    result = []
    for p in patients:
        ref_doctor = assoc_map.get(p["id"], "")
        p["doctor_id"] = ref_doctor
        p["reference_doctor"] = doctor_map.get(ref_doctor, ref_doctor)
        if doctor_id and ref_doctor != doctor_id:
            continue
        result.append(p)
    return result


@doctor_bp.route("/")
@login_required
@role_required("doctor")
def dashboard():
    patients = _list_patients(_current_doctor())
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
    patients = _list_patients(_current_doctor())
    return render_template(
        "doctor/patients.html", patients=patients, current_doctor=_current_doctor()
    )


@doctor_bp.route("/patients/<int:patient_id>")
@login_required
@role_required("doctor")
def patient_detail(patient_id):
    if not _is_assigned(patient_id):
        return render_template(
            "doctor/patient_not_found.html",
            patient_id=patient_id,
            current_doctor=_current_doctor(),
        ), 404
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
    if not _is_assigned(patient_id):
        return jsonify({"error": "paziente non assegnato"}), 404
    period = request.args.get("period", "week")
    trend = _usecases.view_glucose_trend(patient_id, period)
    return jsonify(trend)


@doctor_bp.route("/patients/<int:patient_id>/therapies", methods=["GET", "POST"])
@login_required
@role_required("doctor")
def therapy(patient_id):
    if not _is_assigned(patient_id):
        return render_template(
            "doctor/patient_not_found.html",
            patient_id=patient_id,
            current_doctor=_current_doctor(),
        ), 404
    data = _usecases.view_patient_data(patient_id)
    if data is None:
        return render_template(
            "doctor/patient_not_found.html",
            patient_id=patient_id,
            current_doctor=_current_doctor(),
        ), 404

    editing_id = request.args.get("edit")
    editing = None
    if editing_id:
        for therapy in data["therapies"]:
            if therapy["id"] == editing_id:
                editing = therapy
                break

    form = {}
    errors = {}
    if request.method == "POST":
        v = FormValidator(request.form)
        therapy_id = v.raw("therapy_id")
        drug = v.required("drug", "Farmaco", max_len=120)
        daily_frequency = v.intf("daily_frequency", "Assunzioni giornaliere", minv=1, maxv=24)
        dose = v.required("dose", "Quantità per assunzione", max_len=60)
        indications = v.optional("indications", "Indicazioni", max_len=250)

        if therapy_id and not any(
            t.get("id") == therapy_id for t in data["therapies"]
        ):
            v.fail("drug", "La terapia selezionata non appartiene a questo paziente.")

        if not v.has_errors():
            if therapy_id:
                _usecases.modify_therapy(
                    _current_doctor(), therapy_id, drug=drug, daily_frequency=daily_frequency,
                    dose=dose, indications=indications,
                )
                _system.log_operation(
                    _current_doctor(), "modifica_terapia",
                    f"terapia {therapy_id} paziente {patient_id}",
                )
                flash("Terapia modificata correttamente.", "success")
            else:
                _usecases.prescribe_therapy(
                    _current_doctor(), patient_id, drug, daily_frequency, dose, indications,
                )
                _system.log_operation(
                    _current_doctor(), "prescrizione_terapia",
                    f"paziente {patient_id} farmaco {drug}",
                )
                flash("Terapia prescritta correttamente.", "success")
            return redirect(url_for("doctor.patient_detail", patient_id=patient_id))

        form = {
            "therapy_id": therapy_id,
            "drug": request.form.get("drug", ""),
            "daily_frequency": request.form.get("daily_frequency", ""),
            "dose": request.form.get("dose", ""),
            "indications": request.form.get("indications", ""),
        }
        errors = v.errors

    return render_template(
        "doctor/therapy_form.html",
        data=data,
        editing=editing,
        current_doctor=_current_doctor(),
        form=form,
        errors=errors,
    )


@doctor_bp.route("/patients/<int:patient_id>/clinical", methods=["GET", "POST"])
@login_required
@role_required("doctor")
def clinical_info(patient_id):
    if not _is_assigned(patient_id):
        return render_template(
            "doctor/patient_not_found.html",
            patient_id=patient_id,
            current_doctor=_current_doctor(),
        ), 404
    data = _usecases.view_patient_data(patient_id)
    if data is None:
        return render_template(
            "doctor/patient_not_found.html",
            patient_id=patient_id,
            current_doctor=_current_doctor(),
        ), 404

    form = {}
    errors = {}
    if request.method == "POST":
        v = FormValidator(request.form)
        risk_factors = v.optional("risk_factors", "Fattori di rischio", max_len=500)
        past_pathologies = v.optional("past_pathologies", "Patologie pregresse", max_len=500)
        comorbidities = v.optional("comorbidities", "Comorbidità", max_len=500)
        if not v.has_errors():
            _usecases.update_patient_info(
                _current_doctor(),
                patient_id,
                risk_factors=risk_factors,
                past_pathologies=past_pathologies,
                comorbidities=comorbidities,
            )
            _system.log_operation(
                _current_doctor(), "aggiorna_info_cliniche", f"paziente {patient_id}",
            )
            flash("Informazioni cliniche salvate correttamente.", "success")
            return redirect(url_for("doctor.patient_detail", patient_id=patient_id))
        form = {
            "risk_factors": request.form.get("risk_factors", ""),
            "past_pathologies": request.form.get("past_pathologies", ""),
            "comorbidities": request.form.get("comorbidities", ""),
        }
        errors = v.errors

    info = _usecases.view_patient_info(patient_id)
    return render_template(
        "doctor/clinical_form.html",
        data=data,
        info=info,
        current_doctor=_current_doctor(),
        form=form,
        errors=errors,
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


@doctor_bp.route("/notifications/api")
@login_required
@role_required("doctor")
def notifications_api():
    rows = _usecases.view_notifications(_current_doctor())
    return jsonify(rows)


@doctor_bp.route("/notifications/<notification_id>/read")
@login_required
@role_required("doctor")
def mark_read(notification_id):
    _usecases.mark_notification_read(notification_id)
    return redirect(url_for("doctor.notifications"))