from datetime import date, datetime, timedelta

from utils.csv_utils import CsvManager

PRE_MEAL_MIN = 80
PRE_MEAL_MAX = 130
POST_MEAL_MAX = 180


class SystemUseCases:
    def __init__(self, data_dir="./data"):
        self.data_dir = data_dir
        self.therapies = CsvManager(f"{data_dir}/therapies.csv", delimiter=";")
        self.assunzioni = CsvManager(f"{data_dir}/assunzioni.csv", delimiter=";")
        self.glicemia = CsvManager(f"{data_dir}/glicemia.csv", delimiter=";")
        self.notifications = CsvManager(f"{data_dir}/notifications.csv", delimiter=";")
        self.operations = CsvManager(f"{data_dir}/operations.csv", delimiter=";")

    def _next_id(self, manager) -> int:
        rows = manager.read()
        ids = [int(r["id"]) for r in rows if r.get("id", "").isdigit()]
        return max(ids) + 1 if ids else 1

    def _duplicate_notification(self, doctor_id, patient_id, ntype, message) -> bool:
        return bool(self.notifications.find(
            doctor_id=str(doctor_id),
            patient_id=str(patient_id),
            type=ntype,
            message=message,
        ))

    def _create_notification(self, doctor_id, patient_id, ntype, severity,
                             message) -> dict | None:
        if self._duplicate_notification(doctor_id, patient_id, ntype, message):
            return None
        notification = {
            "id": str(self._next_id(self.notifications)),
            "doctor_id": str(doctor_id),
            "patient_id": str(patient_id),
            "type": ntype,
            "severity": severity,
            "message": message,
            "created_on": date.today().isoformat(),
            "read": "0",
        }
        self.notifications.append(notification)
        return notification

    def run_all_checks(self) -> dict:
        return {
            "missing": self.check_missing_intakes(),
            "consistency": self.verify_intake_consistency(),
            "adherence": self.flag_non_adherence(),
            "glucose": self.flag_out_of_range_glucose(),
        }

    def _active_therapies(self):
        return [t for t in self.therapies.read() if t.get("active", "0") == "1"]

    def _daily_intakes(self, patient_id, drug, day) -> list:
        rows = self.assunzioni.find(patient_id=str(patient_id), drug=drug)
        return [r for r in rows if r.get("assumed_on") == day]

    # UC-S2: Verificare coerenza delle assunzioni con le terapie prescritte
    def verify_intake_consistency(self) -> list:
        findings = []
        intakes = self.assunzioni.read()
        for intake in intakes:
            patient_id = intake["patient_id"]
            drug = intake["drug"]
            therapy = next(
                (t for t in self._active_therapies()
                 if t["patient_id"] == patient_id and t["drug"].lower() == drug.lower()),
                None,
            )
            if therapy is None:
                findings.append({
                    "intake": intake,
                    "issue": "assunzione per farmaco non prescritto o terapia non attiva",
                })
        return findings

    # UC-S3 / UC-S4: sollecitare l'inserimento delle assunzioni e alert al paziente
    def check_missing_intakes(self, reference=None) -> list:
        reference = reference or date.today().isoformat()
        created = []
        for therapy in self._active_therapies():
            patient_id = therapy["patient_id"]
            drug = therapy["drug"]
            expected = 0
            try:
                expected = int(therapy["daily_frequency"])
            except (ValueError, TypeError):
                continue
            done_today = len(self._daily_intakes(patient_id, drug, reference))
            reminder = "completare l'inserimento delle assunzioni"
            if done_today == 0:
                reminder = "assunzione dimenticata per il farmaco"
            if done_today < expected:
                notification = self._create_notification(
                    "", patient_id, "assunzione", "media",
                    f"Paziente {patient_id}: {reminder} {drug} "
                    f"({done_today}/{expected} assunzioni del {reference}).",
                )
                if notification:
                    created.append(notification)
        return created

    # UC-S5: alert al medico per mancata aderenza (> 3 giorni consecutivi)
    def flag_non_adherence(self, max_gap_days=3) -> list:
        today = date.today()
        created = []
        for therapy in self._active_therapies():
            if not therapy.get("prescribed_by"):
                continue
            patient_id = therapy["patient_id"]
            drug = therapy["drug"]
            intakes = self.assunzioni.find(patient_id=str(patient_id), drug=drug)
            last_dates = sorted((r["assumed_on"] for r in intakes), reverse=True)
            if not last_dates:
                anchor = therapy.get("prescribed_on", today.isoformat())
            else:
                anchor = last_dates[0]
            try:
                anchor_date = datetime.strptime(anchor, "%Y-%m-%d").date()
            except ValueError:
                continue
            gap = (today - anchor_date).days
            if gap > max_gap_days:
                notification = self._create_notification(
                    therapy["prescribed_by"], patient_id, "aderenza", "alta",
                    f"Paziente {patient_id}: non aderenza al farmaco {drug} "
                    f"da {gap} giorni consecutivi.",
                )
                if notification:
                    created.append(notification)
        return created

    # UC-S6: segnalare glicemie oltre soglia al medico, per gravità
    def flag_out_of_range_glucose(self) -> list:
        created = []
        rows = self.glicemia.read()
        for row in rows:
            result = self._evaluate_glucose(row)
            if not result:
                continue
            severity, label = result
            doctor = self._reference_doctor(row["patient_id"])
            if not doctor:
                continue
            notification = self._create_notification(
                doctor, row["patient_id"], "glicemia", severity,
                f"Paziente {row['patient_id']}: {label} {row['value']} mg/dL "
                f"il {row['measured_on']}.",
            )
            if notification:
                created.append(notification)
        return created

    def _evaluate_glucose(self, row) -> tuple[str, str] | None:
        try:
            value = float(row["value"].replace(",", "."))
        except (ValueError, TypeError):
            return None
        meal = row.get("meal")
        if meal == "pre":
            if value < PRE_MEAL_MIN:
                return "alta", "ipoglicemia pre-pasto"
            if value > PRE_MEAL_MAX:
                return self._glucose_severity(value), "iperglicemia pre-pasto"
        elif value > POST_MEAL_MAX:
            return self._glucose_severity(value), "iperglicemia post-pasto"
        return None

    def alert_glucose(self, patient_id, value, meal, measured_on) -> dict | None:
        row = {
            "patient_id": str(patient_id),
            "value": str(value),
            "meal": meal,
            "measured_on": measured_on,
        }
        result = self._evaluate_glucose(row)
        if not result or result[0] != "alta":
            return None
        doctor = self._reference_doctor(patient_id)
        if not doctor:
            return None
        return self._create_notification(
            doctor, patient_id, "glicemia", result[0],
            f"Paziente {patient_id}: {result[1]} {value} mg/dL il {measured_on}.",
        )

    def _glucose_severity(self, value) -> str:
        return "alta" if value >= 220 else "media"

    def _reference_doctor(self, patient_id) -> str | None:
        therapy = next(
            (t for t in self._active_therapies()
             if t["patient_id"] == str(patient_id) and t.get("prescribed_by")),
            None,
        )
        return therapy["prescribed_by"] if therapy else None

    # UC-S7: tracciare le operazioni dei medici
    def log_operation(self, doctor_id, operation, details="") -> dict:
        record = {
            "id": str(self._next_id(self.operations)),
            "doctor_id": str(doctor_id),
            "operation": operation,
            "details": details,
            "executed_on": datetime.now().isoformat(timespec="seconds"),
        }
        self.operations.append(record)
        return record

    def view_operations(self, doctor_id=None) -> list:
        rows = self.operations.read()
        if doctor_id is not None:
            rows = [r for r in rows if r["doctor_id"] == str(doctor_id)]
        return rows[::-1]