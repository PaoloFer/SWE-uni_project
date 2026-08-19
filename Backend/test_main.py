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
        f.write("id;patient_id;drug;daily_frequency;dose;indications;"
                "prescribed_by;prescribed_on;modified_by;modified_on;active\n"
                "1;1;prova;5;500mg;dopo i pasti;M1;2026-08-14;;;1\n")
    with open(f"{TEST_DATA}/notifications.csv", "w", encoding="utf-8") as f:
        f.write("id;doctor_id;patient_id;type;severity;message;created_on;read\n")
    with open(f"{TEST_DATA}/patient_info.csv", "w", encoding="utf-8") as f:
        f.write("patient_id;risk_factors;past_pathologies;comorbidities;"
                "updated_by;updated_on\n")
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


setup_test_data()

from main import app

app.config["TESTING"] = True
client = app.test_client()

checks = 0
failed = 0


def ck(label, cond):
    global checks, failed
    checks += 1
    print(("PASS" if cond else "FAIL"), "-", label)
    if not cond:
        failed += 1


def login(user, pwd):
    client.get("/auth/logout")
    return client.post("/auth/login", data={"username": user, "password": pwd})


def body(resp):
    return resp.get_data(as_text=True)


try:
    # ============ A. AUTENTICAZIONE e RUOLI ============
    r = client.post("/auth/login", data={"username": "admin", "password": "errata"})
    ck("A1 credenziali errate -> 401", r.status_code == 401)
    r = login("admin", "admin")
    ck("A2 login admin -> redirect a /system/",
       r.status_code == 302 and "/system/" in r.headers.get("Location", ""))
    login("lverdi", "secret")
    r = client.get("/doctor/")
    ck("A3 accesso a /doctor/ senza sessione valida -> redirect login",
       r.status_code == 302 and "/auth/login" in r.headers.get("Location", ""))
    login("admin", "admin")

    # ============ B. ADMIN: MEDICI e PAZIENTI ============
    for url in ["/admin/", "/admin/patients", "/admin/doctors", "/admin/associations"]:
        ck(f"B pagina admin {url} carica", client.get(url).status_code == 200)

    r = client.post("/admin/doctors/create", data={
        "name": "Anna", "surname": "Bianchi", "email": "anna@example.com",
        "username": "abianchi", "password": "secret"})
    ck("B1 create medico M2 -> redirect", r.status_code == 302)
    r = client.post("/admin/doctors/create", data={
        "name": "Mario", "surname": "Verdi", "email": "mario@example.com",
        "username": "mverdi", "password": "secret"})
    ck("B2 create medico M3 -> redirect", r.status_code == 302)
    r = client.post("/admin/doctors/create", data={
        "name": "Anna", "surname": "Bianchi", "email": "x@x.it",
        "username": "abianchi", "password": "altra"})
    ck("B3 username duplicato rifiutato (flash errore)", r.status_code == 302 and
       "gi\u00e0 esistente" in body(client.get("/admin/doctors")))

    for name, surname, user, doctor in [
        ("Luca", "Verdi", "lverdi", "M2"),
        ("Carlo", "Neri", "cneri", "M2"),
        ("Sara", "Blu", "sblu", "M3"),
    ]:
        r = client.post("/admin/patients/create", data={
            "name": name, "surname": surname, "phone": "333", "doctor_id": doctor,
            "username": user, "password": "secret"})
        ck(f"B4 create paziente {user} -> redirect", r.status_code == 302)

    b = body(client.get("/admin/associations"))
    ck("B5 associazioni mostrano coppie",
       "Luca Verdi" in b and "Carlo Neri" in b and "Anna Bianchi" in b)

    login("abianchi", "secret")
    r = login("abianchi", "secret")
    ck("B6 login medico M2 -> redirect a /doctor/",
       r.status_code == 302 and "/doctor/" in r.headers.get("Location", ""))
    r = login("abianchi", "secret")
    ck("B7 benvenuto mostra nome medico", r.status_code == 302)
    login("admin", "admin")

    r = client.post("/admin/doctors/M2/edit", data={
        "name": "Anna", "surname": "Bianchi", "email": "anna@example.com",
        "username": "abianchi", "password": "nuova"})
    ck("B8 edit medico -> redirect", r.status_code == 302)
    r = login("abianchi", "nuova")
    ck("B9 login con nuova password funziona", r.status_code == 302)

    # ============ C. PAZIENTE: UC-P1..P6 ============
    login("lverdi", "secret")

    r = client.post("/patient/glicemia", data={
        "measured_on": "2099-01-01", "measured_at": "08:00", "meal": "pre", "value": "100"})
    ck("P1 data futura rifiutata e form ricaricato",
       r.status_code == 200 and "data futura" in body(r) and "field-error" in body(r))
    r = client.post("/patient/glicemia", data={
        "measured_on": "2026-08-19", "measured_at": "08:00", "meal": "pre", "value": "5000"})
    ck("P2 valore fuori range rifiutato", r.status_code == 200 and "non può superare" in body(r))
    r = client.post("/patient/glicemia", data={
        "measured_on": "2026-08-19", "measured_at": "08:00", "meal": "pranzo", "value": "118"})
    ck("P3 momento pasto non valido rifiutato", r.status_code == 200 and "consentiti" in body(r))
    r = client.post("/patient/glicemia", data={
        "measured_on": "2026-08-19", "measured_at": "08:00", "meal": "pre", "value": "118"})
    ck("P4 glicemia valida -> redirect + conferma", r.status_code == 302)
    b = body(client.get("/patient/glicemia"))
    ck("P5 conferma salvataggio visibile e salvata", "salvata correttamente" in b and "118" in b)

    r = client.post("/patient/glicemia", data={
        "measured_on": "2026-08-19", "measured_at": "09:00", "meal": "pre", "value": "250"})
    ck("P6 glicemia alta salvata e genera alert", r.status_code == 302)

    r = client.post("/patient/sintomi", data={"reported_on": "2026-08-19", "symptom": ""})
    ck("P7 sintomo vuoto rifiutato", r.status_code == 200 and "obbligatorio" in body(r))
    r = client.post("/patient/sintomi", data={"reported_on": "2026-08-19", "symptom": "nausea"})
    ck("P8 sintomo valido -> conferma", r.status_code == 302 and
       "segnalato correttamente" in body(client.get("/patient/sintomi")))

    r = client.post("/patient/assunzioni", data={
        "assumed_on": "2099-01-01", "assumed_at": "", "drug": "prova", "quantity": "1"})
    ck("P9 assunzione data futura rifiutata", r.status_code == 200 and "data futura" in body(r))
    r = client.post("/patient/assunzioni", data={
        "assumed_on": "2026-08-19", "assumed_at": "", "drug": "", "quantity": "1"})
    ck("P10 assunzione senza farmaco rifiutata", r.status_code == 200 and "obbligatorio" in body(r))
    r = client.post("/patient/assunzioni", data={
        "assumed_on": "2026-08-19", "assumed_at": "", "drug": "prova", "quantity": "1 compressa"})
    ck("P11 assunzione valida -> conferma", r.status_code == 302 and
       "registrata correttamente" in body(client.get("/patient/assunzioni")))

    r = client.post("/patient/concomitanti", data={"type": "altro", "description": "x", "period": ""})
    ck("P12 tipo non valido rifiutato", r.status_code == 200 and "consentiti" in body(r))
    r = client.post("/patient/concomitanti",
                    data={"type": "patologia", "description": "ipertensione", "period": ""})
    ck("P13 segnalazione valida -> conferma", r.status_code == 302 and
       "registrata correttamente" in body(client.get("/patient/concomitanti")))

    r = client.post("/patient/contatto-medico", data={"message": "   "})
    ck("P14 messaggio vuoto rifiutato", r.status_code == 200 and "obbligatorio" in body(r))
    r = client.post("/patient/contatto-medico", data={"message": "Ho una domanda"})
    ck("P15 contatto valido -> conferma invio", r.status_code == 302 and
       "inviato correttamente" in body(client.get("/patient/contatto-medico")))

    ck("P16 paziente vede le proprie notifiche",
       "Le mie notifiche" in body(client.get("/patient/notifications")))

    r = client.get("/doctor/")
    ck("P17 paziente bloccato dall'area medico -> redirect login",
       r.status_code == 302 and "/auth/login" in r.headers.get("Location", ""))

    r = client.get("/patient/notifications/api")
    ck("P18 paziente chiama api notifiche", r.status_code == 200 and isinstance(r.get_json(), list))
    r = client.post("/patient/notifications/read-all")
    ck("P19 paziente segna tutte come lette -> JSON ok",
       r.status_code == 200 and r.get_json().get("ok") is True)
    ck("P20 pagina notifiche paziente ha filtri",
       "Tutte" in body(client.get("/patient/notifications")))

    # ============ D. MEDICO: UC-M1..M6 ============
    login("abianchi", "nuova")
    b = body(client.get("/doctor/"))
    ck("D1 dashboard mostra nome completo medico",
       "Benvenuto, diabetologo <strong>Anna Bianchi</strong>" in b)
    ck("D2 menu mostra badge notifiche non lette", "nav-badge" in b)

    r = client.post("/doctor/patients/2/therapies", data={
        "drug": "", "daily_frequency": "2", "dose": "500mg", "indications": ""})
    ck("M1 farmaco vuoto rifiutato", r.status_code == 200 and "obbligatorio" in body(r))
    r = client.post("/doctor/patients/2/therapies", data={
        "drug": "prova", "daily_frequency": "0", "dose": "500mg", "indications": ""})
    ck("M2 frequenza 0 rifiutata", r.status_code == 200 and "almeno" in body(r))
    r = client.post("/doctor/patients/2/therapies", data={
        "drug": "metformina", "daily_frequency": "2", "dose": "500mg", "indications": "dopo i pasti"})
    ck("M3 prescrizione valida -> redirect", r.status_code == 302)
    b = body(client.get("/doctor/patients/2"))
    ck("M4 conferma prescrizione e terapia visibile",
       "prescritta correttamente" in b and "metformina" in b)

    r = client.post("/doctor/patients/2/therapies", data={
        "therapy_id": "1", "drug": "prova",
        "daily_frequency": "6", "dose": "500mg", "indications": "x"})
    ck("M5 modifica terapia di altro paziente rifiutata",
       r.status_code == 200 and "non appartiene" in body(r))
    r = client.post("/doctor/patients/2/therapies", data={
        "therapy_id": "2", "drug": "metformina",
        "daily_frequency": "3", "dose": "600mg", "indications": "sera"})
    ck("M6 modifica terapia propria -> conferma", r.status_code == 302 and
       "modificata correttamente" in body(client.get("/doctor/patients/2")))

    r = client.get("/doctor/patients/2")
    ck("M7 scheda paziente proprio accessibile", r.status_code == 200 and "Terapie prescritte" in body(r))
    ck("M8 dettaglio mostra sezioni dati", "Rilevazioni glicemia" in body(r))
    r = client.get("/doctor/patients/1")
    ck("M9 paziente di altro medico -> 404", r.status_code == 404)
    r = client.get("/doctor/patients/4")
    ck("M10 paziente di altro medico -> 404", r.status_code == 404)

    r = client.get("/doctor/patients/2/trend?period=week")
    ck("M11 trend settimanale JSON ok", r.status_code == 200 and isinstance(r.get_json(), list))
    r = client.get("/doctor/patients/2/trend?period=month")
    ck("M12 trend mensile JSON ok", r.status_code == 200)
    r = client.get("/doctor/patients/1/trend?period=week")
    ck("M13 trend di altro paziente -> 404", r.status_code == 404)

    r = client.post("/doctor/patients/2/clinical", data={
        "risk_factors": "fumatore", "past_pathologies": "", "comorbidities": "ipertensione"})
    ck("M14 info cliniche salvate -> conferma", r.status_code == 302 and
       "salvate correttamente" in body(client.get("/doctor/patients/2")))
    r = client.post("/doctor/patients/2/clinical", data={
        "risk_factors": "x" * 600, "past_pathologies": "", "comorbidities": ""})
    ck("M15 info cliniche fuori lunghezza rifiutate", r.status_code == 200 and "caratteri" in body(r))

    r = client.get("/doctor/notifications/api")
    payload = r.get_json() or []
    ck("M16 medico vede notifica contatto paziente",
       any("Ho una domanda" in n.get("message", "") for n in payload))
    ck("M17 medico vede alert glicemia alta",
       any("iperglicemia" in n.get("message", "") for n in payload))
    ck("M17b api notifiche include nome paziente",
       any("Luca Verdi" == n.get("patient_name", "") for n in payload))
    if payload:
        nid = payload[0]["id"]
        ck("M18 segna notifica come letta -> redirect",
           client.get(f"/doctor/notifications/{nid}/read").status_code == 302)
        r = client.post(f"/doctor/notifications/{nid}/read")
        ck("M18b segna come letta via POST -> JSON ok",
           r.status_code == 200 and r.get_json().get("ok") is True)
    r = client.post("/doctor/notifications/read-all")
    ck("M18c segna tutte come lette -> JSON ok",
       r.status_code == 200 and r.get_json().get("count", 0) >= 1)
    ck("M18d dopo lettura non restano notifiche non lette",
       client.get("/doctor/notifications/api").get_json() == [])

    b = body(client.get("/doctor/patients"))
    ck("M19 lista pazienti M2 ha i propri pazienti", "Verdi" in b and "Neri" in b)
    ck("M20 lista pazienti M2 esclude quelli altrui", "Blu" not in b)

    # ============ E. SISTEMA: UC-S2..S7 ============
    from system.usecases import SystemUseCases
    from utils.csv_utils import CsvManager

    login("admin", "admin")
    r = client.get("/system/operations")
    ck("S2 registro operazioni carica", r.status_code == 200)

    su = SystemUseCases(TEST_DATA)
    ck("S3 riferimento medico paziente 1 = M1", su._reference_doctor("1") == "M1")

    created = su.check_missing_intakes("2026-08-19")
    ck("S4 assunzioni mancanti generano notifiche",
       any(n["type"] == "assunzione" for n in created))
    adh = su.flag_non_adherence()
    ck("S5 non aderenza oltre 3 giorni segnalata",
       any(n["type"] == "aderenza" for n in adh))

    assunzioni = CsvManager(f"{TEST_DATA}/assunzioni.csv", delimiter=";")
    assunzioni.append({"patient_id": "2", "assumed_on": "2026-08-19", "assumed_at": "",
                       "drug": "metformina", "quantity": "1000 mg"})
    for _ in range(3):
        assunzioni.append({"patient_id": "2", "assumed_on": "2026-08-19", "assumed_at": "",
                           "drug": "metformina", "quantity": "1"})
    issues = su.verify_intake_consistency()
    ck("S6 quantità superiore alla dose segnalata",
       any("quantità" in i["issue"] and "superiore" in i["issue"] for i in issues))
    ck("S7 frequenza giornaliera superata segnalata",
       any("frequenza giornaliera" in i["issue"] for i in issues))

    glicemia = CsvManager(f"{TEST_DATA}/glicemia.csv", delimiter=";")
    glicemia.append({"patient_id": "2", "measured_on": "2026-08-18",
                     "measured_at": "14:30", "meal": "post", "value": "240"})
    alerts = su.flag_out_of_range_glucose()
    ck("S8 glicemie oltre soglia generano alert",
       any(n["type"] == "glicemia" for n in alerts))
    ops = su.view_operations()
    ck("S9 operazioni dei medici tracciate",
       any(o["operation"] == "prescrizione_terapia" for o in ops))

    r = client.post("/system/checks")
    ck("S1 esito controlli automatici carica",
       r.status_code == 200 and "Esito controlli automatici" in body(r))

    # ============ F. ELIMINAZIONI ============
    login("admin", "admin")
    r = client.post("/admin/patients/4/delete")
    ck("F1 delete paziente -> redirect", r.status_code == 302)
    r = login("sblu", "secret")
    ck("F2 paziente eliminato non accede più", r.status_code == 401)
    login("admin", "admin")
    r = client.post("/admin/doctors/M3/delete")
    ck("F3 delete medico -> redirect", r.status_code == 302)
    r = login("mverdi", "secret")
    ck("F4 medico eliminato non accede più", r.status_code == 401)

    print(f"DONE - {checks} controlli, {failed} falliti")
finally:
    os.environ.pop("DATA_DIR", None)
    if os.path.exists(TEST_DATA):
        shutil.rmtree(TEST_DATA)