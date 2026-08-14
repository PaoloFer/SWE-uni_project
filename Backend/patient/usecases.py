from datetime import date, datetime

from utils.csv_utils import CsvManager


class PatientUseCases:
    def __init__(self, data_dir="./data"):
        self.data_dir = data_dir
        self.glicemia = CsvManager(f"{data_dir}/glicemia.csv", delimiter=";")
        self.symptoms = CsvManager(f"{data_dir}/symptoms.csv", delimiter=";")
        self.assunzioni = CsvManager(f"{data_dir}/assunzioni.csv", delimiter=";")
        self.concomitant = CsvManager(f"{data_dir}/concomitant.csv", delimiter=";")
        self.contacts = CsvManager(f"{data_dir}/contacts.csv", delimiter=";")
        self.therapies = CsvManager(f"{data_dir}/therapies.csv", delimiter=";")
        self.notifications = CsvManager(f"{data_dir}/notifications.csv", delimiter=";")

    def _next_id(self, manager) -> int:
        rows = manager.read()
        ids = [int(r["id"]) for r in rows if r.get("id", "").isdigit()]
        return max(ids) + 1 if ids else 1

    # UC-P1: Inserire rilevazione di glicemia
    def record_glicemia(self, patient_id, measured_on, measured_at, meal, value):
        reading = {
            "patient_id": str(patient_id),
            "measured_on": measured_on,
            "measured_at": measured_at or "",
            "meal": meal,
            "value": str(value),
        }
        self.glicemia.append(reading)
        return reading

    # UC-P2: Aggiungere sintomo
    def add_symptom(self, patient_id, reported_on, symptom):
        entry = {
            "patient_id": str(patient_id),
            "reported_on": reported_on,
            "symptom": symptom,
        }
        self.symptoms.append(entry)
        return entry

    # UC-P3: Registrare assunzione di farmaco/insulina
    def record_assunzione(self, patient_id, assumed_on, assumed_at, drug, quantity):
        entry = {
            "patient_id": str(patient_id),
            "assumed_on": assumed_on,
            "assumed_at": assumed_at or "",
            "drug": drug,
            "quantity": str(quantity),
        }
        self.assunzioni.append(entry)
        return entry

    # UC-P4: Segnalare sintomi, patologie e/o terapie concomitanti
    def report_concomitant(self, patient_id, ctype, description, period):
        entry = {
            "patient_id": str(patient_id),
            "type": ctype,
            "description": description,
            "period": period or "",
        }
        self.concomitant.append(entry)
        return entry

    # UC-P5: Contattare il medico di riferimento
    def contact_doctor(self, patient_id, message):
        associations = CsvManager(f"{self.data_dir}/associations.csv", delimiter=";")
        assoc = next(
            (r for r in associations.read() if r.get("patient_id") == str(patient_id)), None
        )
        doctor_id = assoc.get("doctor_id", "") if assoc else ""

        contact = {
            "id": str(self._next_id(self.contacts)),
            "patient_id": str(patient_id),
            "doctor_id": doctor_id,
            "message": message,
            "created_on": date.today().isoformat(),
        }
        self.contacts.append(contact)

        if doctor_id:
            notification = {
                "id": str(self._next_id(self.notifications)),
                "doctor_id": doctor_id,
                "patient_id": str(patient_id),
                "type": "contact",
                "severity": "info",
                "message": f"Richiesta del paziente: {message}",
                "created_on": datetime.now().isoformat(timespec="minutes"),
                "read": "0",
            }
            self.notifications.append(notification)

        return contact

    # Helper: terapie attive del paziente
    def list_therapies(self, patient_id, active_only=True):
        rows = self.therapies.find(patient_id=str(patient_id))
        if active_only:
            rows = [r for r in rows if r.get("active", "1") == "1"]
        return rows

    # Helper: medico di riferimento del paziente
    def view_reference_doctor(self, patient_id):
        associations = CsvManager(f"{self.data_dir}/associations.csv", delimiter=";")
        assoc = next(
            (r for r in associations.read() if r.get("patient_id") == str(patient_id)), None
        )
        if not assoc or not assoc.get("doctor_id"):
            return None
        doctors = CsvManager(f"{self.data_dir}/doctors.csv", delimiter=";")
        record = next(
            (r for r in doctors.read() if r.get("id") == assoc["doctor_id"]), None
        )
        if record is None:
            return None
        return {
            "id": record.get("id"),
            "name": record.get("name"),
            "surname": record.get("surname"),
            "email": record.get("email"),
        }

    # UC-P6: Consultare le proprie notifiche
    def view_notifications(self, patient_id, unread_only=True):
        rows = [
            r for r in self.notifications.find(patient_id=str(patient_id))
            if not r.get("doctor_id")
        ]
        if unread_only:
            rows = [r for r in rows if r.get("read", "0") == "0"]
        return rows[::-1]

    def mark_notification_read(self, notification_id, patient_id):
        rows = self.notifications.read()
        for row in rows:
            if row["id"] == str(notification_id) and row["patient_id"] == str(patient_id):
                row["read"] = "1"
                self.notifications.write(rows)
                return row
        return None