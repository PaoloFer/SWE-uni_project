from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

import config
from auth.usecases import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

_usecases = AuthService(config.DATA_DIR)

ROLE_HOME = {
    "doctor": "doctor.dashboard",
    "patient": "patient.dashboard",
    "system": "system.dashboard",
}


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = _usecases.authenticate(username, password)
        if user is None:
            return render_template("auth/login.html", error="Credenziali non valide"), 401
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["entity_id"] = user["entity_id"]
        return redirect(url_for(ROLE_HOME[user["role"]]))
    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    user = _usecases.authenticate(username, password)
    if user is None:
        return jsonify({"error": "Credenziali non valide"}), 401
    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "entity_id": user["entity_id"],
    })


@auth_bp.route("/api/me")
def api_me():
    if "user_id" not in session:
        return jsonify({"error": "Non autenticato"}), 401
    return jsonify({
        "id": session["user_id"],
        "username": session["username"],
        "role": session["role"],
        "entity_id": session["entity_id"],
    })