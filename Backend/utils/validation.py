from datetime import date, datetime

_DATE_FMT = "%Y-%m-%d"
_TIME_FMT = "%H:%M"


class FormValidator:
    """Raccoglie errori di validazione dei dati inviati da un form."""

    def __init__(self, form):
        self.form = form
        self.errors = {}

    def has_errors(self) -> bool:
        return bool(self.errors)

    def fail(self, field, message) -> None:
        self.errors.setdefault(field, []).append(message)

    def raw(self, field) -> str:
        return str(self.form.get(field, "") or "").strip()

    def required(self, field, label=None, max_len=None) -> str:
        label = label or field
        value = self.raw(field)
        if not value:
            self.fail(field, f"Il campo {label} è obbligatorio.")
            return ""
        if max_len is not None and len(value) > max_len:
            self.fail(field, f"Il campo {label} non può superare {max_len} caratteri.")
            return ""
        return value

    def optional(self, field, label=None, max_len=None) -> str:
        label = label or field
        value = self.raw(field)
        if value and max_len is not None and len(value) > max_len:
            self.fail(field, f"Il campo {label} non può superare {max_len} caratteri.")
            return ""
        return value

    def datef(self, field, label=None, not_future=False) -> str:
        label = label or field
        value = self.raw(field)
        if not value:
            self.fail(field, f"Il campo {label} è obbligatorio.")
            return ""
        try:
            parsed = datetime.strptime(value, _DATE_FMT).date()
        except ValueError:
            self.fail(field, f"Il campo {label} deve essere una data valida nel formato AAAA-MM-GG.")
            return ""
        if not_future and parsed > date.today():
            self.fail(field, f"Il campo {label} non può essere una data futura.")
            return ""
        return value

    def timef(self, field, label=None) -> str:
        label = label or field
        value = self.raw(field)
        if not value:
            return ""
        try:
            datetime.strptime(value, _TIME_FMT)
        except ValueError:
            self.fail(field, f"Il campo {label} deve essere un orario valido nel formato HH:MM.")
            return ""
        return value

    def intf(self, field, label=None, minv=None, maxv=None) -> str:
        label = label or field
        value = self.raw(field)
        if not value:
            self.fail(field, f"Il campo {label} è obbligatorio.")
            return ""
        try:
            num = int(value)
        except ValueError:
            self.fail(field, f"Il campo {label} deve essere un numero intero.")
            return ""
        if minv is not None and num < minv:
            self.fail(field, f"Il campo {label} deve essere almeno {minv}.")
            return ""
        if maxv is not None and num > maxv:
            self.fail(field, f"Il campo {label} non può superare {maxv}.")
            return ""
        return str(num)

    def numberf(self, field, label=None, minv=None, maxv=None) -> str:
        label = label or field
        value = self.raw(field).replace(",", ".")
        if not value:
            self.fail(field, f"Il campo {label} è obbligatorio.")
            return ""
        try:
            num = float(value)
        except ValueError:
            self.fail(field, f"Il campo {label} deve essere un numero valido.")
            return ""
        if minv is not None and num < minv:
            self.fail(field, f"Il campo {label} deve essere almeno {minv}.")
            return ""
        if maxv is not None and num > maxv:
            self.fail(field, f"Il campo {label} non può superare {maxv}.")
            return ""
        return value

    def choice(self, field, choices, label=None) -> str:
        label = label or field
        value = self.raw(field)
        if value not in choices:
            self.fail(field, f"Il valore del campo {label} non è tra quelli consentiti.")
            return ""
        return value