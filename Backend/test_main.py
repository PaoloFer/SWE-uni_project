import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BACKUP = os.path.join(os.path.dirname(__file__), ".test_data_backup")


def backup_data():
    if os.path.exists(BACKUP):
        shutil.rmtree(BACKUP)
    shutil.copytree(DATA_DIR, BACKUP)


def restore_data():
    shutil.rmtree(DATA_DIR)
    shutil.copytree(BACKUP, DATA_DIR)


from main import app

app.config["TESTING"] = True
client = app.test_client()


def check(label, cond):
    print(("PASS" if cond else "FAIL"), "-", label)


backup_data()
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

    # 11. Doctor patients list shows reference doctor column
    r = client.get("/doctor/patients")
    body = r.get_data(as_text=True)
    check("doctor patients list has reference", "Anna Bianchi" in body)

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
    su = SystemUseCases("./data")
    check("reference doctor patient 1 = M1", su._reference_doctor("1") == "M1")

    print("DONE")
finally:
    restore_data()