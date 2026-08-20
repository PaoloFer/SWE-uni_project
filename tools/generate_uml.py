"""Genera diagrammi UML (casi d'uso e sequenza) in formato PlantUML.

Lo script:
  1. Scansiona il backend (routes/usecases/UC comments) come verifica;
  2. Produce docs/uml/usecases.puml e docs/uml/sequence-*.puml;
  3. Produce docs/uml/routes.puml con l'inventario delle route reali;
  4. Produce docs/uml/all.puml che include tutti i diagrammi.

Uso:
  python tools/generate_uml.py        # genera i file nella cartella docs/uml
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "Backend"
OUT_DIR = ROOT / "docs" / "uml"

# ---------------------------------------------------------------------------
# 1. Inventario reale dal codice (verifica automatica)
# ---------------------------------------------------------------------------


def load_routes() -> dict[str, list[str]]:
    """Importa l'app Flask e raggruppa le route per blueprint."""
    sys.path.insert(0, str(BACKEND))
    # La variabile d'ambiente WINEPREFIX/altro non serve; import diretto.
    cwd = os.getcwd()
    os.chdir(BACKEND)
    try:
        from main import app

        groups: dict[str, list[str]] = defaultdict(list)
        for rule in app.url_map.iter_rules():
            parts = rule.endpoint.split(".")
            bp = parts[0] if len(parts) > 1 else "(root)"
            methods = ",".join(sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"}))
            groups[bp].append(f"{rule.rule} [{methods}] -> {rule.endpoint}")
        for lst in groups.values():
            lst.sort()
        return dict(sorted(groups.items()))
    finally:
        os.chdir(cwd)


def usecase_comments() -> list[tuple[str, str]]:
    """Estrae i commenti 'UC-...' dai file usecases del backend."""
    found: list[tuple[str, str]] = []
    pattern = re.compile(r"UC-([A-Z]\d+):?\s+(.+)")
    for path in [
        BACKEND / "patient" / "usecases.py",
        BACKEND / "doctor" / "usecases.py",
        BACKEND / "system" / "usecases.py",
    ]:
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            m = pattern.search(line)
            if m and "UC-1" not in m.group(1):
                found.append((m.group(1), m.group(2).strip()))
    return found


def dict_uc(rows: list[tuple[str, str]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for code, title in rows:
        mapping.setdefault(code, title)
    return mapping

# ---------------------------------------------------------------------------
# 2. Modello dei casi d'uso (curato)
# ---------------------------------------------------------------------------

ACTORS = [
    ("PAZ", "Paziente"),
    ("MED", "Diabetologo"),
    ("RESP", "Responsabile del servizio"),
    ("SIST", "Sistema automatico"),
]

# (codice, titolo, attore, endpoint di riferimento)
USE_CASES = [
    {"code": "P1", "title": "Inserire rilevazione di glicemia", "actor": "PAZ", "endpoint": "patient.glicemia"},
    {"code": "P2", "title": "Aggiungere sintomo", "actor": "PAZ", "endpoint": "patient.symptoms"},
    {"code": "P3", "title": "Registrare assunzione di farmaco/insulina", "actor": "PAZ", "endpoint": "patient.assunzioni"},
    {"code": "P4", "title": "Segnalare patologie/terapie concomitanti", "actor": "PAZ", "endpoint": "patient.concomitant"},
    {"code": "P5", "title": "Contattare il medico di riferimento", "actor": "PAZ", "endpoint": "patient.contact"},
    {"code": "P6", "title": "Consultare le proprie notifiche", "actor": "PAZ", "endpoint": "patient.notifications"},
    {"code": "M1", "title": "Prescrivere una terapia", "actor": "MED", "endpoint": "doctor.therapy"},
    {"code": "M2", "title": "Modificare una terapia", "actor": "MED", "endpoint": "doctor.therapy"},
    {"code": "M3", "title": "Visualizzare i dati di un paziente", "actor": "MED", "endpoint": "doctor.patient_detail"},
    {"code": "M4", "title": "Visualizzare l'andamento della glicemia", "actor": "MED", "endpoint": "doctor.patient_trend"},
    {"code": "M5", "title": "Aggiornare le informazioni cliniche del paziente", "actor": "MED", "endpoint": "doctor.clinical_info"},
    {"code": "M6", "title": "Consultare le proprie notifiche", "actor": "MED", "endpoint": "doctor.notifications"},
    {"code": "A1", "title": "Gestire l'anagrafica dei pazienti", "actor": "RESP", "endpoint": "admin.patients"},
    {"code": "A2", "title": "Gestire l'anagrafica dei medici", "actor": "RESP", "endpoint": "admin.doctors"},
    {"code": "A3", "title": "Associare pazienti e medici", "actor": "RESP", "endpoint": "admin.associations"},
    {"code": "A4", "title": "Consultare il registro delle operazioni", "actor": "RESP", "endpoint": "system.operations"},
    {"code": "S1", "title": "Eseguire i controlli automatici", "actor": "SIST", "endpoint": "system.dashboard"},
    {"code": "S2", "title": "Verificare la coerenza assunzioni-terapie", "actor": "SIST", "endpoint": "system.run_checks"},
    {"code": "S3", "title": "Sollecitare le assunzioni mancanti (paziente)", "actor": "SIST", "endpoint": "system.run_checks"},
    {"code": "S4", "title": "Alert al paziente per assunzioni mancanti", "actor": "SIST", "endpoint": "system.run_checks"},
    {"code": "S5", "title": "Alert al medico per mancata aderenza", "actor": "SIST", "endpoint": "system.run_checks"},
    {"code": "S6", "title": "Segnalare glicemie fuori soglia per gravità", "actor": "SIST", "endpoint": "system.run_checks"},
    {"code": "S7", "title": "Tracciare le operazioni dei medici", "actor": "SIST", "endpoint": "system.run_checks"},
]

# relazione include/estendi: (da, a, tipo)
EXTENDS = [
    ("S1", "S2", "include"),
    ("S1", "S4", "include"),
    ("S1", "S5", "include"),
    ("S1", "S6", "include"),
]

# ---------------------------------------------------------------------------
# 3. Sequenze
# ---------------------------------------------------------------------------

# ogni flusso: nome file, titolo, partecipanti [(kind, alias, label)], steps
# kind: a=actor, p=participant (control/entity), d=database
FLOWS = [
    {
        "file": "sequence-login.puml",
        "title": "UC trasversale - Autenticazione",
        "participants": [
            ("a", "U", "Utente"),
            ("p", "R", "Routes auth"),
            ("p", "SVC", "AuthService"),
            ("d", "DB", "data/users.csv"),
        ],
        "steps": [
            ("m", "U", "R", "GET /auth/login"),
            ("r", "R", "U", "pagina di login"),
            ("m", "U", "R", "POST /auth/login (username, password)"),
            ("m", "R", "SVC", "authenticate(username, password)"),
            ("m", "SVC", "DB", "verifica password (hash scrypt)"),
            ("r", "DB", "SVC", "utente / None"),
            ("alt", "Credenziali valide"),
            ("r", "SVC", "R", "ruolo ed entity_id"),
            ("m", "R", "U", "redirect all'area di ruolo"),
            ("else", "Credenziali errate"),
            ("r", "R", "U", "login con messaggio d'errore"),
            ("end",),
        ],
    },
    {
        "file": "sequence-p1-glicemia.puml",
        "title": "UC-P1 - Inserimento rilevazione di glicemia",
        "participants": [
            ("a", "PAZ", "Paziente"),
            ("p", "R", "Routes patient.glicemia"),
            ("p", "UC", "PatientUseCases"),
            ("d", "GL", "data/glicemia.csv"),
            ("p", "SYS", "SystemUseCases"),
            ("d", "NOT", "data/notifications.csv"),
        ],
        "steps": [
            ("m", "PAZ", "R", "POST /patient/glicemia (data, ora, pasto, valore)"),
            ("m", "R", "UC", "record_glicemia(patient_id, ...)"),
            ("m", "UC", "GL", "append rilevazione"),
            ("r", "UC", "R", "rilevazione salvata"),
            ("opt", "Valore fuori soglia (pre: 80-130, post: <=180)"),
            ("m", "R", "SYS", "alert_glucose(patient_id, value, meal, date)"),
            ("m", "SYS", "NOT", "crea notifica alert glicemia (gravità)"),
            ("r", "SYS", "R", "notifica creata per il medico di riferimento"),
            ("end",),
            ("r", "R", "PAZ", "flash conferma + redirect /patient/glicemia"),
        ],
    },
    {
        "file": "sequence-p5-contatto.puml",
        "title": "UC-P5 - Contattare il medico di riferimento",
        "participants": [
            ("a", "PAZ", "Paziente"),
            ("p", "R", "Routes patient.contact"),
            ("p", "UC", "PatientUseCases"),
            ("d", "AS", "data/associations.csv"),
            ("d", "CT", "data/contacts.csv"),
            ("d", "NOT", "data/notifications.csv"),
        ],
        "steps": [
            ("m", "PAZ", "R", "POST /patient/contatto-medico (messaggio)"),
            ("m", "R", "UC", "contact_doctor(patient_id, message)"),
            ("m", "UC", "AS", "trova medico di riferimento"),
            ("r", "UC", "AS", "doctor_id (se assegnato)"),
            ("m", "UC", "CT", "append contatto"),
            ("opt", "Esiste un medico di riferimento"),
            ("m", "UC", "NOT", "crea notifica type=contact per il medico"),
            ("end",),
            ("r", "UC", "R", "contatto registrato"),
            ("r", "R", "PAZ", "flash conferma + redirect"),
        ],
    },
    {
        "file": "sequence-m1-terapia.puml",
        "title": "UC-M1 - Prescrivere una terapia",
        "participants": [
            ("a", "MED", "Diabetologo"),
            ("p", "R", "Routes doctor.therapy"),
            ("p", "UC", "DoctorUseCases"),
            ("d", "TH", "data/therapies.csv"),
            ("d", "OP", "data/operations.csv"),
        ],
        "steps": [
            ("m", "MED", "R", "POST /doctor/patients/{id}/therapies (farmaco, freq, dose)"),
            ("m", "R", "UC", "prescribe_therapy(patient_id, ...)"),
            ("m", "UC", "TH", "append prescrizione (active=1)"),
            ("r", "UC", "R", "terapia prescritta"),
            ("m", "R", "OP", "traccia operazione del medico (UC-S7)"),
            ("r", "R", "MED", "flash conferma + scheda paziente"),
        ],
    },
    {
        "file": "sequence-s6-notifica.puml",
        "title": "UC-S5/S6 - Azioni automatiche di controllo",
        "participants": [
            ("p", "WK", "SystemBackgroundWorker"),
            ("p", "SYS", "SystemUseCases"),
            ("d", "GL", "data/glicemia.csv"),
            ("d", "AS", "data/assunzioni.csv"),
            ("d", "TH", "data/therapies.csv"),
            ("d", "NOT", "data/notifications.csv"),
        ],
        "steps": [
            ("loop", "ogni intervallo configurato (30s)"),
            ("m", "WK", "SYS", "run_all_checks()"),
            ("m", "SYS", "GL", "flag_out_of_range_glucose()"),
            ("m", "SYS", "AS", "check_missing_intakes()"),
            ("m", "SYS", "TH", "verify_intake_consistency()"),
            ("alt", "glicemia fuori soglia / aderenza mancata / assunzioni incoerenti"),
            ("m", "SYS", "NOT", "crea notifiche dedicate (gravità definita)"),
            ("r", "SYS", "NOT", "elenco notifiche create (deduplicate)"),
            ("else", "nessuna anomalia"),
            ("r", "SYS", "WK", "nessuna notifica da emettere"),
            ("end",),
            ("end",),
        ],
    },
]

PWMS = "skinparam backgroundColor #FFFFFF\nskinparam defaultFontName Arial\n"

# ---------------------------------------------------------------------------
# 4. Generazione
# ---------------------------------------------------------------------------


def puml_usecases() -> str:
    uc = dict_uc(usecase_comments())
    out = [
        "@startuml usecases",
        "skinparam shadowing false",
        "skinparam actorStyle awesome",
        "left to right direction",
        "",
        "' verifica: commenti UC trovati nel codice",
    ]
    for code, title in uc.items():
        out.append(f"'  - {code}: {title}")
    out.append("")

    for alias, label in ACTORS:
        out.append(f'actor "{label}" as {alias}')
    out.append("")

    groups = [
        ("Dominio paziente", ["P1", "P2", "P3", "P4", "P5", "P6"]),
        ("Dominio diabetologo", ["M1", "M2", "M3", "M4", "M5", "M6"]),
        ("Dominio amministrativo", ["A1", "A2", "A3", "A4"]),
        ("Sistema automatico", ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]),
    ]
    by_code = {uc["code"]: uc for uc in USE_CASES}
    for box, codes in groups:
        out.append(f'rectangle "{box}" {{')
        for code in codes:
            u = by_code[code]
            endpoint = u["endpoint"]
            out.append(
                f'  usecase "**{code}** {u["title"]}\\n({endpoint})" as UC_{code}'
            )
        out.append("}")
    out.append("")

    for u in USE_CASES:
        out.append(f'{u["actor"]} --> UC_{u["code"]}')
    out.append("")

    for src, dst, rel in EXTENDS:
        out.append(f'UC_{src} ..> UC_{dst} : {rel}')
    out.append("")
    out.append("@enduml")
    return "\n".join(out) + "\n"


def puml_sequence(flow: dict) -> str:
    out = [f'@startuml {os.path.splitext(flow["file"])[0]}']
    out.append(f'title {flow["title"]}')
    out.append("autonumber")
    for kind, alias, label in flow["participants"]:
        if kind == "a":
            out.append(f'actor "{label}" as {alias}')
        elif kind == "d":
            out.append(f'database "{label}" as {alias}')
        else:
            out.append(f'control "{label}" as {alias}')
    out.append("")
    indent = ""
    for step in flow["steps"]:
        tag = step[0]
        if tag == "act":
            pass
        elif tag in ("alt", "else", "loop", "opt"):
            if tag == "else":
                out.append(indent + "else " + step[1])
            else:
                out.append(indent + f'{tag} {step[1]}')
            indent += "  "
        elif tag == "end":
            indent = indent[:-2]
            out.append(indent + "end")
        elif tag == "m":
            out.append(indent + f'{step[1]} -> {step[2]} : {step[3]}')
        elif tag == "r":
            out.append(indent + f'{step[1]} --> {step[2]} : {step[3]}')
        elif tag == "note":
            out.append(indent + f'note right : {step[1]}')
    out.append("")
    out.append("@enduml")
    return "\n".join(out) + "\n"


def puml_routes(groups: dict[str, list[str]]) -> str:
    out = [
        "@startuml routes",
        "skinparam shadowing false",
        "left to right direction",
        "",
        "' Inventario reale delle route Flask, raggruppate per blueprint",
    ]
    for bp, rules in groups.items():
        out.append(f'node "{bp}" as {bp}_bp {{')
        for rule in rules:
            label = rule.replace('"', '\\"')
            out.append(f'  card "{label}"')
        out.append("}")
    out.append("")
    out.append("@enduml")
    return "\n".join(out) + "\n"


def puml_all(files: list[str]) -> str:
    lines = ["@startuml all", ""]
    for f in files:
        lines.append(f"!include {f}")
    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    routes = load_routes()
    uc_comments = usecase_comments()
    codes_in_code = {c for c, _ in uc_comments} | {"S1"}  # S1 controlli automatici
    uc_defined = {u["code"] for u in USE_CASES}

    # verifica YAML non serve; segnala riferimenti endpoint mancanti
    known = set()
    for rules in routes.values():
        for rule in rules:
            known.add(rule.split("-> ")[-1].strip())
    stale = [
        u["code"]
        for u in USE_CASES
        if u["endpoint"] not in known
    ]
    if stale:
        print("ATTENZIONE: endpoint non trovati per i UC:", ", ".join(stale))

    # scorre gli UC non presenti nel codice -> informazione
    missing_in_code = uc_defined - codes_in_code
    print("UC nel modello ma non nei commenti codice:",
          sorted(missing_in_code) or "nessuno")

    files = ["usecases.puml"]

    (OUT_DIR / "usecases.puml").write_text(puml_usecases(), encoding="utf-8")

    for flow in FLOWS:
        fname = flow["file"]
        (OUT_DIR / fname).write_text(puml_sequence(flow), encoding="utf-8")
        files.append(fname)

    (OUT_DIR / "routes.puml").write_text(puml_routes(routes), encoding="utf-8")
    files.append("routes.puml")

    (OUT_DIR / "all.puml").write_text(puml_all(files), encoding="utf-8")

    print(f"\nGenerati {len(files) + 1} file in {OUT_DIR}:")
    for f in ["all.puml"] + files:
        size = (OUT_DIR / f).stat().st_size
        print(f"  {f:28s} {size:6d} B")


if __name__ == "__main__":
    main()