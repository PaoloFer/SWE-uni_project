from flask import Blueprint, redirect, render_template, session, url_for

from auth.decorators import login_required, role_required

system_bp = Blueprint("system", __name__, url_prefix="/system")


@system_bp.route("/")
@login_required
@role_required("system")
def dashboard():
    return render_template(
        "system/dashboard.html",
        current_username=session.get("username"),
    )


@system_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))