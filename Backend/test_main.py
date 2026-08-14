import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))

PROJECT_DATA = os.path.join(os.path.dirname(__file__), "data")
TEST_DATA = os.path.join(os.path.dirname(__file__), ".test_data")

EMPTY = {
    "assunzioni.csv": "patient_id;assumed_on;assumed_at;drug;quantity\n",
    "concomitant.csv": "patient_id;type;description;period\n",
    "contacts.csv": "id;patient_id;doctor_id;message;created_on\n",
    "operations.csv": "id;doctor_id;operation;details;executed_on\n",
    "symptoms.csv": "patient_id;reported_on;symptom\n",
}


def setup_test_data():
    if os.path.exists(TEST_DATA):
        shutil.rmtree(TEST_DATA)
    os.makedirs(TEST_DATA)
    with open(f"{TEST_DATA}/associations.csv", "w", encoding="utf-8") as f:
        f.write("patient_id;doctor_id\n1;M1\n")
    with open(f"{TEST_DATA}/doctors.csv", "w", encoding="utf-8") as f:
        f.write("id;name;surname;email\nM1;Mario;Rossi;mario.rossi@example.com\n")
    with open(f"{TEST_DATA}/patient.csv", "w", encoding="utf-8") as f:
        f.write("id;surname;name;phone\n1;Giacomi;Francesco;34512349\n")
    with open(f"{TEST_DATA}/therapies.csv", "w", encoding="utf-8") as f:
        f.write("id;patient_id;drug;daily_frequency;dose;indications;prescribed_by;prescribed_on;modified_by;modified_on;active\n"
                "1;1;prova;5;500mg;dopo i pasti;M1;2026-08-14;;;1\n")
    with open(f"{TEST_DATA}/notifications.csv", "w", encoding="utf-8") as f:
        f.write("id;doctor_id;patient_id;type;severity;message;created_on;read\n")
    with open(f"{TEST_DATA}/patient_info.csv", "w", encoding="utf-8") as f:
        f.write("patient_id;risk_factors;past_pathologies;comorbidities;updated_by;updated_on\n")
    with open(f"{TEST_DATA}/glicemia.csv", "w", encoding="utf-8") as f:
        f.write("patient_id;measured_on;measured_at;meal;value\n")
    for name, content in EMPTY.items():
        with open(f"{TEST_DATA}/{name}", "w", encoding="utf-8") as f:
            f.write(content)
    with open(f"{PROJECT_DATA}/users.csv", encoding="utf-8") as src:
        lines = src.readlines()
    with open(f"{TEST_DATA}/users.csv", "w", encoding="utf-8") as f:
        f.write("".join(lines[:4]))
    os.environ["DATA_DIR"] = TEST_DATA


def teardown_test_data():
    os.environ.pop("DATA_DIR", None)
    if os.path.exists(TEST_DATA):
        shutil.rmtree(TEST_DATA)


setup_test_data()

from main import app

app.config["TESTING"] = True
client = app.test_client()


def check(label, cond):
    print(("PASS" if cond else "FAIL"), "-", label)


try:
    # 1. Login admin
    r = client.post("/auth/login", data={"username": "admin", "password": "admin"})
    check("login admin", r.status_code == 302 and "/system/" in r.headers.get("Location", ""))

    # 2. Admin pages load
    for url in ["/admin/", "/admin/patients", "/admin/doctors", "/admin/associations"]:
        r = client.get(url)
        check(f"GET {url}", r.status_code == 200)

    # 3. Create a doctor
    r = client.post("/admin/doctors/create", data={
        "name": "Anna", "surname": "Bianchi", "email": "anna@example.com",
        "username": "abianchi", "password": "secret",
    })
    check("create doctor -> redirect", r.status_code == 302)

    # 4. Create a patient assigned to new doctor
    r = client.post("/admin/patients/create", data={
        "name": "Luca", "surname": "Verdi", "phone": "333", "doctor_id": "M2",
        "username": "lverdi", "password": "secret",
    })
    check("create patient -> redirect", r.status_code == 302)

    # 5. Check associations page lists the new pair
    r = client.get("/admin/associations")
    body = r.get_data(as_text=True)
    check("associations page shows pair", "Luca Verdi" in body and "Anna Bianchi" in body)

    # 6. Login as new patient
    client.get("/auth/logout")
    r = client.post("/auth/login", data={"username": "lverdi", "password": "secret"})
    check("login new patient", r.status_code == 302 and "/patient/" in r.headers.get("Location", ""))

    # 7. Patient dashboard shows reference doctor
    r = client.get("/patient/")
    body = r.get_data(as_text=True)
    check("patient dashboard shows doctor", "Anna Bianchi" in body)

    # 8. Patient contact page shows email
    r = client.get("/patient/contatto-medico")
    body = r.get_data(as_text=True)
    check("patient contact shows email", "anna@example.com" in body)

    # 9. Patient sends contact -> creates notification for doctor
    r = client.post("/patient/contatto-medico", data={"message": "Ho una domanda"})
    check("patient contact post -> redirect", r.status_code == 302)

    # 10. Login as doctor M2 and see notification
    client.get("/auth/logout")
    r = client.post("/auth/login", data={"username": "abianchi", "password": "secret"})
    check("login doctor M2", r.status_code == 302 and "/doctor/" in r.headers.get("Location", ""))
    r = client.get("/doctor/notifications/api")
    payload = r.get_json() or []
    check("doctor sees contact notification", any("Ho una domanda" in n.get("message", "") for n in payload))

    # 10b. Doctor patient detail shows assunzioni/concomitanti sections
    r = client.get("/doctor/patients/2")
    body = r.get_data(as_text=True)
    check("doctor patient detail has assunzioni section", "Assunzioni registrate dal paziente" in body)
    check("doctor patient detail has concomitant section", "Segnalazioni concomitanti" in body)

    # 11. Doctor patients list shows only own patients
    r = client.get("/doctor/patients")
    body = r.get_data(as_text=True)
    check("doctor patients list has own patient", "Verdi" in body and "Luca" in body)
    check("doctor patients list has reference", "Anna Bianchi" in body)
    check("doctor patients list excludes other doctor's patient", "Giacomi" not in body)

    # 11b. Doctor cannot open another doctor's patient detail
    r = client.get("/doctor/patients/1")
    check("doctor blocked from other doctor's patient", r.status_code == 404)
    r = client.get("/doctor/patients/1/trend")
    check("doctor blocked from other doctor's patient trend", r.status_code == 404)

    # 12. Update doctor password via admin
    client.get("/auth/logout")
    client.post("/auth/login", data={"username": "admin", "password": "admin"})
    r = client.post("/admin/doctors/M2/edit", data={
        "name": "Anna", "surname": "Bianchi", "email": "anna@example.com",
        "username": "abianchi", "password": "nuova",
    })
    check("edit doctor -> redirect", r.status_code == 302)
    client.get("/auth/logout")
    r = client.post("/auth/login", data={"username": "abianchi", "password": "nuova"})
    check("login with new password", r.status_code == 302)

    # 13. Admin delete patient
    client.get("/auth/logout")
    client.post("/auth/login", data={"username": "admin", "password": "admin"})
    r = client.post("/admin/patients/2/delete")
    check("delete patient -> redirect", r.status_code == 302)
    client.get("/auth/logout")
    r = client.post("/auth/login", data={"username": "lverdi", "password": "secret"})
    check("deleted patient can't login", r.status_code == 401)

    # 14. Admin delete doctor
    client.post("/auth/login", data={"username": "admin", "password": "admin"})
    r = client.post("/admin/doctors/M2/delete")
    check("delete doctor -> redirect", r.status_code == 302)

    # 15. system usecase reference doctor from associations (patient 1 -> M1)
    from system.usecases import SystemUseCases
    su = SystemUseCases(TEST_DATA)
    check("reference doctor patient 1 = M1", su._reference_doctor("1") == "M1")

    # 16. UC-S2: quantity above prescribed dose is flagged
    from utils.csv_utils import CsvManager
    assunzioni = CsvManager(f"{TEST_DATA}/assunzioni.csv", delimiter=";")
    assunzioni.append({
        "patient_id": "1", "assumed_on": "2026-08-14", "assumed_at": "08:00",
        "drug": "prova", "quantity": "1000 mg",
    })
    issues = su.verify_intake_consistency()
    check("UC-S2 flags quantity above dose", any("quantità" in i["issue"] and "superiore" in i["issue"] for i in issues))

    # 17. UC-S2: daily frequency exceeded is flagged (therapy prova freq 5, record 6 intakes)
    for _ in range(6):
        assunzioni.append({
            "patient_id": "1", "assumed_on": "2026-08-13", "assumed_at": "",
            "drug": "prova", "quantity": "1",
        })
    issues = su.verify_intake_consistency()
    check("UC-S2 flags frequency exceeded", any("frequenza giornaliera" in i["issue"] for i in issues))

    print("DONE")
finally:
    teardown_test_data()