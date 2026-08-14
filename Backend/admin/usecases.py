from auth.usecases import AuthService
from utils.csv_utils import CsvManager


class AdminUseCases:
    def __init__(self, data_dir="./data"):
        self.data_dir = data_dir
        self.patients = CsvManager(f"{data_dir}/patient.csv", delimiter=";")
        self.doctors = CsvManager(f"{data_dir}/doctors.csv", delimiter=";")
        self.associations = CsvManager(f"{data_dir}/associations.csv", delimiter=";")
        self.auth = AuthService(data_dir)

    # ---------- helper ----------
    def _next_patient_id(self) -> int:
        ids = [int(r["id"]) for r in self.patients.read() if r.get("id", "").isdigit()]
        return max(ids) + 1 if ids else 1

    def _next_doctor_id(self) -> str:
        ids = [
            int(r["id"][1:])
            for r in self.doctors.read()
            if r.get("id", "").startswith("M") and r["id"][1:].isdigit()
        ]
        return f"M{max(ids) + 1 if ids else 1}"

    def _reference_doctor(self, patient_id: str) -> str | None:
        rows = self.associations.find(patient_id=str(patient_id))
        return rows[0]["doctor_id"] if rows else None

    # ---------- anagrafica medici ----------
    def list_doctors(self) -> list[dict]:
        doctors = self.doctors.read()
        result = []
        for doctor in doctors:
            user = self.auth.get_user_by_entity(doctor["id"], role="doctor")
            patients = self.associations.find(doctor_id=doctor["id"])
            result.append({
                **doctor,
                "username": user["username"] if user else "",
                "patient_count": len(patients),
            })
        return result

    def create_doctor(self, name, surname, email, username, password) -> dict:
        doctor = {
            "id": self._next_doctor_id(),
            "name": name,
            "surname": surname,
            "email": email or "",
        }
        self.doctors.append(doctor)
        self.auth.create_user(username, password, "doctor", doctor["id"])
        return doctor

    def update_doctor(self, doctor_id, name=None, surname=None, email=None,
                      username=None, password=None) -> dict | None:
        rows = self.doctors.read()
        for row in rows:
            if row["id"] == str(doctor_id):
                if name is not None:
                    row["name"] = name
                if surname is not None:
                    row["surname"] = surname
                if email is not None:
                    row["email"] = email
                self.doctors.write(rows)
                user = self.auth.get_user_by_entity(doctor_id, role="doctor")
                if user:
                    self.auth.update_user(user["id"], username=username, password=password)
                return row
        return None

    def delete_doctor(self, doctor_id) -> None:
        self.doctors.delete(id=str(doctor_id))
        user = self.auth.get_user_by_entity(doctor_id, role="doctor")
        if user:
            self.auth.delete_user(user["id"])
        for row in self.associations.find(doctor_id=str(doctor_id)):
            self.associations.delete(patient_id=row["patient_id"], doctor_id=row["doctor_id"])

    # ---------- anagrafica pazienti ----------
    def list_patients(self) -> list[dict]:
        result = []
        for patient in self.patients.read():
            doctor_id = self._reference_doctor(patient["id"])
            doctor = None
            if doctor_id:
                doctors = self.doctors.find(id=doctor_id)
                doctor = doctors[0] if doctors else None
            user = self.auth.get_user_by_entity(patient["id"], role="patient")
            result.append({
                **patient,
                "doctor_id": doctor_id or "",
                "reference_doctor": (
                    f"{doctor['name']} {doctor['surname']}" if doctor else ""
                ),
                "username": user["username"] if user else "",
            })
        return result

    def create_patient(self, name, surname, phone, username, password,
                       doctor_id=None) -> dict:
        patient = {
            "id": str(self._next_patient_id()),
            "name": name,
            "surname": surname,
            "phone": phone or "",
        }
        self.patients.append(patient)
        self.auth.create_user(username, password, "patient", patient["id"])
        if doctor_id:
            self.associations.append({"patient_id": patient["id"], "doctor_id": doctor_id})
        return patient

    def update_patient(self, patient_id, name=None, surname=None, phone=None,
                       doctor_id=None, username=None, password=None) -> dict | None:
        rows = self.patients.read()
        for row in rows:
            if row["id"] == str(patient_id):
                if name is not None:
                    row["name"] = name
                if surname is not None:
                    row["surname"] = surname
                if phone is not None:
                    row["phone"] = phone
                self.patients.write(rows)
                if doctor_id is not None:
                    self.assign_doctor(patient_id, doctor_id)
                user = self.auth.get_user_by_entity(patient_id, role="patient")
                if user:
                    self.auth.update_user(user["id"], username=username, password=password)
                return row
        return None

    def delete_patient(self, patient_id) -> None:
        self.patients.delete(id=str(patient_id))
        user = self.auth.get_user_by_entity(patient_id, role="patient")
        if user:
            self.auth.delete_user(user["id"])
        self.associations.delete(patient_id=str(patient_id))

    # ---------- relazione paziente - medico ----------
    def list_associations(self) -> list[dict]:
        result = []
        for assoc in self.associations.read():
            patients = self.patients.find(id=assoc["patient_id"])
            doctors = self.doctors.find(id=assoc["doctor_id"])
            patient = patients[0] if patients else {}
            doctor = doctors[0] if doctors else {}
            result.append({
                "patient_id": assoc["patient_id"],
                "patient_name": f"{patient.get('name', '')} {patient.get('surname', '')}".strip(),
                "doctor_id": assoc["doctor_id"],
                "doctor_name": f"{doctor.get('name', '')} {doctor.get('surname', '')}".strip(),
            })
        return result

    def assign_doctor(self, patient_id, doctor_id) -> None:
        self.associations.delete(patient_id=str(patient_id))
        if doctor_id:
            self.associations.append({
                "patient_id": str(patient_id),
                "doctor_id": str(doctor_id),
            })

    def unassign_doctor(self, patient_id) -> None:
        self.associations.delete(patient_id=str(patient_id))
