import csv
from typing import Any


class CsvManager:
    def __init__(self, path: str):
        self.path = path

    def read(self) -> list[dict[str, Any]]:
        with open(self.path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def write(self, data: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
        rows = list(data)
        if fieldnames is None:
            fieldnames = list(rows[0].keys()) if rows else []
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def append(self, data: dict[str, Any] | list[dict[str, Any]]) -> None:
        rows = [data] if isinstance(data, dict) else data
        if not rows:
            return
        if not self._exists():
            self.write(rows)
            return
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writerows(rows)

    def find(self, **filters: Any) -> list[dict[str, Any]]:
        return [row for row in self.read() if all(row.get(k) == v for k, v in filters.items())]

    def delete(self, **filters: Any) -> int:
        rows = self.read()
        remaining = [row for row in rows if not all(row.get(k) == v for k, v in filters.items())]
        removed = len(rows) - len(remaining)
        if removed and remaining:
            self.write(remaining)
        elif removed:
            self._clear()
        return removed

    def _exists(self) -> bool:
        try:
            with open(self.path, newline="", encoding="utf-8"):
                return True
        except FileNotFoundError:
            return False

    def _clear(self) -> None:
        with open(self.path, "w", newline="", encoding="utf-8"):
            pass