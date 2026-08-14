from werkzeug.security import check_password_hash, generate_password_hash

from utils.csv_utils import CsvManager


class AuthService:
    def __init__(self, data_dir="./data"):
        self.users = CsvManager(f"{data_dir}/users.csv", delimiter=";")

    def authenticate(self, username: str, password: str) -> dict | None:
        rows = self.users.find(username=username)
        if not rows:
            return None
        user = rows[0]
        if not check_password_hash(user["password_hash"], password):
            return None
        return user

    def create_user(self, username: str, password: str, role: str, entity_id: str) -> dict:
        if self.users.find(username=username):
            raise ValueError("username già esistente")
        user = {
            "id": str(self._next_id()),
            "username": username,
            "password_hash": generate_password_hash(password),
            "role": role,
            "entity_id": str(entity_id),
        }
        self.users.append(user)
        return user

    def _next_id(self) -> int:
        ids = [int(r["id"]) for r in self.users.read() if r.get("id", "").isdigit()]
        return max(ids) + 1 if ids else 1