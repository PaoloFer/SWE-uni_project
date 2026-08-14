from utils.csv_utils import CsvManager


class PatientUseCases:
    def __init__(self, data_dir="./data"):
        self.data_dir = data_dir
        self.notifications = CsvManager(f"{data_dir}/notifications.csv", delimiter=";")

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