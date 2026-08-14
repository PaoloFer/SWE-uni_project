import csv
import threading
from typing import Any

_LOCK = threading.RLock()


class CsvManager:
    def __init__(self, path: str, delimiter: str = ",", has_header: bool = True):
        self.path = path
        self.delimiter = delimiter
        self.has_header = has_header

    def read(self) -> list[dict[str, Any]]:
        with _LOCK:
            return self._read_unsafe()

    def write(self, data: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
        with _LOCK:
            self._write_unsafe(data, fieldnames)

    def append(self, data: dict[str, Any] | list[dict[str, Any]]) -> None:
        with _LOCK:
            self._append_unsafe(data)

    def find(self, **filters: Any) -> list[dict[str, Any]]:
        return [row for row in self.read() if all(row.get(k) == v for k, v in filters.items())]

    def delete(self, **filters: Any) -> int:
        with _LOCK:
            rows = self._read_unsafe()
            remaining = [row for row in rows if not all(row.get(k) == v for k, v in filters.items())]
            removed = len(rows) - len(remaining)
            if removed and remaining:
                self._write_unsafe(remaining)
            elif removed:
                self._clear_unsafe()
            return removed

    def _read_unsafe(self) -> list[dict[str, Any]]:
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

    def _write_unsafe(self, data: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
        rows = list(data)
        if fieldnames is None:
            fieldnames = list(rows[0].keys()) if rows else []
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=self.delimiter)
            writer.writeheader()
            writer.writerows(rows)

    def _append_unsafe(self, data: dict[str, Any] | list[dict[str, Any]]) -> None:
        rows = [data] if isinstance(data, dict) else data
        if not rows:
            return
        if not self._exists_unsafe() or self._is_empty_unsafe():
            self._write_unsafe(rows)
            return
        with open(self.path, "r", newline="", encoding="utf-8") as f:
            content = f.read()
        prefix = "" if content.endswith("\n") else "\n"
        fieldnames = self._header_unsafe()
        if not fieldnames:
            fieldnames = list(rows[0].keys())
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            if prefix:
                f.write(prefix)
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=self.delimiter)
            writer.writerows(rows)

    def _header_unsafe(self) -> list[str]:
        try:
            with open(self.path, newline="", encoding="utf-8") as f:
                first = f.readline().rstrip("\r\n")
        except FileNotFoundError:
            return []
        if not first:
            return []
        return first.split(self.delimiter)

    def _is_empty_unsafe(self) -> bool:
        try:
            with open(self.path, newline="", encoding="utf-8") as f:
                return not any(f.read().strip())
        except FileNotFoundError:
            return True

    def _exists_unsafe(self) -> bool:
        try:
            with open(self.path, newline="", encoding="utf-8"):
                return True
        except FileNotFoundError:
            return False

    def _clear_unsafe(self) -> None:
        with open(self.path, "w", newline="", encoding="utf-8"):
            pass