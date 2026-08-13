import csv
from typing import Any


class CsvManager:
    def __init__(self, path: str, delimiter: str = ",", has_header: bool = True):
        self.path = path
        self.delimiter = delimiter
        self.has_header = has_header

    def read(self) -> list[dict[str, Any]]:
        rows = []
        with open(self.path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            data = list(reader)
        if not data:
            return rows
        if self.has_header:
            header, body = data[0], data[1:]
        else:
            header, body = list(range(1, len(data[0]) + 1)), data
        for line in body:
            if any(line):
                rows.append(dict(zip(header, line)))
        return rows

    def write(self, data: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
        rows = list(data)
        if fieldnames is None:
            fieldnames = list(rows[0].keys()) if rows else []
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=self.delimiter)
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