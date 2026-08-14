from datetime import date

from utils.csv_utils import CsvManager


class DoctorUseCases:
    def __init__(self, data_dir="./data"):
        self.data_dir = data_dir
        self.therapies = CsvManager(f"{data_dir}/therapies.csv", delimiter=";")
        self.patient_info = CsvManager(f"{data_dir}/patient_info.csv", delimiter=";")
        self.notifications = CsvManager(f"{data_dir}/notifications.csv", delimiter=";")
        self.glicemia = CsvManager(f"{data_dir}/glicemia.csv", delimiter=";")
        self.symptoms = CsvManager(f"{data_dir}/symptoms.csv", delimiter=";")
        self.assunzioni = CsvManager(f"{data_dir}/assunzioni.csv", delimiter=";")
        self.concomitant = CsvManager(f"{data_dir}/concomitant.csv", delimiter=";")

    def _next_id(self, manager) -> int:
        rows = manager.read()
        ids = [int(r["id"]) for r in rows if r.get("id", "").isdigit()]
        return max(ids) + 1 if ids else 1

    def _patient_exists(self, patient_id) -> bool:
        return any(
            row.get("id") == str(patient_id)
            for row in CsvManager(f"{self.data_dir}/patient.csv", delimiter=";").read()
        )

    # UC-M1: Prescrivere una terapia
    def prescribe_therapy(self, doctor_id, patient_id, drug, daily_frequency,
                          dose, indications=""):
        therapy = {
            "id": str(self._next_id(self.therapies)),
            "patient_id": str(patient_id),
            "drug": drug,
            "daily_frequency": str(daily_frequency),
            "dose": str(dose),
            "indications": indications,
            "prescribed_by": str(doctor_id),
            "prescribed_on": date.today().isoformat(),
            "modified_by": "",
            "modified_on": "",
            "active": "1",
        }
        self.therapies.append(therapy)
        return therapy

    # UC-M2: Modificare una terapia
    def modify_therapy(self, doctor_id, therapy_id, **changes):
        allowed = {"drug", "daily_frequency", "dose", "indications", "active"}
        rows = self.therapies.read()
        for row in rows:
            if row["id"] == str(therapy_id):
                for key, value in changes.items():
                    if key in allowed:
                        row[key] = str(value)
                row["modified_by"] = str(doctor_id)
                row["modified_on"] = date.today().isoformat()
                self.therapies.write(rows)
                return row
        return None

    def list_therapies(self, patient_id):
        return self.therapies.find(patient_id=str(patient_id))

    # UC-M3: Visualizzare i dati di un paziente
    def view_patient_data(self, patient_id):
        patients = CsvManager(f"{self.data_dir}/patient.csv", delimiter=";")
        record = next((r for r in patients.read() if r.get("id") == str(patient_id)), None)
        if record is None:
            return None
        return {
            "patient_id": patient_id,
            "name": record.get("name"),
            "surname": record.get("surname"),
            "therapies": self.therapies.find(patient_id=str(patient_id)),
            "glicemia": self.glicemia.find(patient_id=str(patient_id)),
            "symptoms": self.symptoms.find(patient_id=str(patient_id)),
            "assunzioni": self.assunzioni.find(patient_id=str(patient_id)),
            "concomitant": self.concomitant.find(patient_id=str(patient_id)),
            "clinical_info": self.patient_info.find(patient_id=str(patient_id)),
        }

    # UC-M4: Visualizzare dati in forma sintetica (andamento glicemia)
    def view_glucose_trend(self, patient_id, period="week"):
        from datetime import datetime

        if period not in ("week", "month"):
            raise ValueError("period must be 'week' or 'month'")

        rows = self.glicemia.find(patient_id=str(patient_id))
        buckets = {}
        for row in rows:
            try:
                value = float(row["value"].replace(",", "."))
                measured = datetime.strptime(row["measured_on"], "%Y-%m-%d")
            except (ValueError, KeyError):
                continue
            if period == "week":
                key = measured.isocalendar()[:2]
            else:
                key = (measured.year, measured.month)
            buckets.setdefault(key, []).append(value)

        trend = []
        for key in sorted(buckets):
            values = buckets[key]
            if period == "week":
                label = f"settimana {key[1]} {key[0]}"
            else:
                label = f"{key[1]:02d}/{key[0]}"
            trend.append({
                "period": label,
                "avg": round(sum(values) / len(values), 1),
                "min": min(values),
                "max": max(values),
                "count": len(values),
            })
        return trend

    # UC-M5: Aggiornare informazioni cliniche del paziente
    def update_patient_info(self, doctor_id, patient_id, risk_factors=None,
                            past_pathologies=None, comorbidities=None):
        rows = self.patient_info.read()
        for row in rows:
            if row["patient_id"] == str(patient_id):
                if risk_factors is not None:
                    row["risk_factors"] = risk_factors
                if past_pathologies is not None:
                    row["past_pathologies"] = past_pathologies
                if comorbidities is not None:
                    row["comorbidities"] = comorbidities
                row["updated_by"] = str(doctor_id)
                row["updated_on"] = date.today().isoformat()
                self.patient_info.write(rows)
                return row

        info = {
            "patient_id": str(patient_id),
            "risk_factors": risk_factors or "",
            "past_pathologies": past_pathologies or "",
            "comorbidities": comorbidities or "",
            "updated_by": str(doctor_id),
            "updated_on": date.today().isoformat(),
        }
        self.patient_info.append(info)
        return info

    def view_patient_info(self, patient_id):
        rows = self.patient_info.find(patient_id=str(patient_id))
        return rows[0] if rows else None

    # UC-M6: Consultare le proprie notifiche
    def view_notifications(self, doctor_id, unread_only=True):
        rows = self.notifications.find(doctor_id=str(doctor_id))
        if unread_only:
            rows = [r for r in rows if r.get("read", "0") == "0"]
        return rows

    def mark_notification_read(self, notification_id):
        rows = self.notifications.read()
        for row in rows:
            if row["id"] == str(notification_id):
                row["read"] = "1"
                self.notifications.write(rows)
                return row
        return None