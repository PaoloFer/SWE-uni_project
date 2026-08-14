from flask import Blueprint, redirect, render_template, session, url_for

import config
from auth.decorators import login_required, role_required
from system.usecases import SystemUseCases

system_bp = Blueprint("system", __name__, url_prefix="/system")

_usecases = SystemUseCases(config.DATA_DIR)


@system_bp.before_request
def _require_system():
    if session.get("role") != "system":
        return redirect(url_for("auth.login"))


@system_bp.route("/")
@login_required
@role_required("system")
def dashboard():
    return render_template(
        "system/dashboard.html",
        current_username=session.get("username"),
    )


@system_bp.route("/checks", methods=["POST"])
@login_required
@role_required("system")
def run_checks():
    results = _usecases.run_all_checks()
    return render_template(
        "system/checks.html",
        missing=results["missing"],
        consistency=results["consistency"],
        adherence=results["adherence"],
        glucose=results["glucose"],
        current_username=session.get("username"),
    )


@system_bp.route("/operations")
@login_required
@role_required("system")
def operations():
    rows = _usecases.view_operations()
    return render_template(
        "system/operations.html",
        operations=rows,
        current_username=session.get("username"),
    )


@system_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))