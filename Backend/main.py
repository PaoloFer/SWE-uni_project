import os

from flask import Flask, redirect, url_for

app = Flask(
    __name__,
    template_folder="../Frontend/templates",
    static_folder="../Frontend/static",
)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

from auth.routes import auth_bp
from doctor.routes import doctor_bp
from patient.routes import patient_bp
from system.routes import system_bp

app.register_blueprint(auth_bp)
app.register_blueprint(doctor_bp)
app.register_blueprint(patient_bp)
app.register_blueprint(system_bp)


def _start_background_worker() -> None:
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        from system.background import SystemBackgroundWorker

        interval = int(os.environ.get("SYSTEM_CHECK_INTERVAL", "30"))
        worker = SystemBackgroundWorker(interval)
        worker.start()
        app.extensions["system_worker"] = worker


@app.route("/")
def hello():
    return redirect(url_for("auth.login"))


if __name__ == "__main__":
    _start_background_worker()
    app.run(debug=True)
