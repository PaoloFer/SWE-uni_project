from flask import Blueprint, flash, redirect, render_template, request, url_for

from admin.usecases import AdminUseCases
from auth.decorators import login_required, role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

_usecases = AdminUseCases("./data")


@admin_bp.route("/")
@login_required
@role_required("system")
def dashboard():
    return render_template(
        "admin/dashboard.html",
        current_username=_session_username(),
    )


@admin_bp.route("/patients")
@login_required
@role_required("system")
def patients():
    return render_template(
        "admin/patients.html",
        current_username=_session_username(),
        patients=_usecases.list_patients(),
        doctors=_usecases.list_doctors(),
    )


@admin_bp.route("/patients/create", methods=["POST"])
@login_required
@role_required("system")
def create_patient():
    try:
        _usecases.create_patient(
            request.form["name"],
            request.form["surname"],
            request.form.get("phone", ""),
            request.form["username"],
            request.form["password"],
            request.form.get("doctor_id") or None,
        )
        flash("Paziente creato correttamente.")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.patients"))


@admin_bp.route("/patients/<patient_id>/edit", methods=["POST"])
@login_required
@role_required("system")
def edit_patient(patient_id):
    try:
        _usecases.update_patient(
            patient_id,
            name=request.form.get("name"),
            surname=request.form.get("surname"),
            phone=request.form.get("phone"),
            doctor_id=request.form.get("doctor_id") or None,
            username=request.form.get("username") or None,
            password=request.form.get("password") or None,
        )
        flash("Paziente aggiornato correttamente.")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.patients"))


@admin_bp.route("/patients/<patient_id>/delete", methods=["POST"])
@login_required
@role_required("system")
def delete_patient(patient_id):
    _usecases.delete_patient(patient_id)
    flash("Paziente eliminato.")
    return redirect(url_for("admin.patients"))


@admin_bp.route("/doctors")
@login_required
@role_required("system")
def doctors():
    return render_template(
        "admin/doctors.html",
        current_username=_session_username(),
        doctors=_usecases.list_doctors(),
    )


@admin_bp.route("/doctors/create", methods=["POST"])
@login_required
@role_required("system")
def create_doctor():
    try:
        _usecases.create_doctor(
            request.form["name"],
            request.form["surname"],
            request.form.get("email", ""),
            request.form["username"],
            request.form["password"],
        )
        flash("Medico creato correttamente.")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.doctors"))


@admin_bp.route("/doctors/<doctor_id>/edit", methods=["POST"])
@login_required
@role_required("system")
def edit_doctor(doctor_id):
    try:
        _usecases.update_doctor(
            doctor_id,
            name=request.form.get("name"),
            surname=request.form.get("surname"),
            email=request.form.get("email"),
            username=request.form.get("username") or None,
            password=request.form.get("password") or None,
        )
        flash("Medico aggiornato correttamente.")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.doctors"))


@admin_bp.route("/doctors/<doctor_id>/delete", methods=["POST"])
@login_required
@role_required("system")
def delete_doctor(doctor_id):
    _usecases.delete_doctor(doctor_id)
    flash("Medico eliminato.")
    return redirect(url_for("admin.doctors"))


@admin_bp.route("/associations")
@login_required
@role_required("system")
def associations():
    return render_template(
        "admin/associations.html",
        current_username=_session_username(),
        associations=_usecases.list_associations(),
        patients=_usecases.list_patients(),
        doctors=_usecases.list_doctors(),
    )


@admin_bp.route("/associations/assign", methods=["POST"])
@login_required
@role_required("system")
def assign_doctor():
    patient_id = request.form.get("patient_id")
    doctor_id = request.form.get("doctor_id")
    _usecases.assign_doctor(patient_id, doctor_id or None)
    flash("Associazione aggiornata.")
    return redirect(url_for("admin.associations"))


def _session_username() -> str:
    from flask import session

    return session.get("username", "")
