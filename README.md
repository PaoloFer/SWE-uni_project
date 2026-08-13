# Progetto Uni

## Struttura

- `Backend/` — API Flask
- `Frontend/` — applicazione client

## Backend (Flask)

### Prerequisiti

- [Python 3.12](https://www.python.org/downloads/) installato e disponibile da terminale (`python --version`).

### Setup del virtualenv

Il progetto usa un ambiente Python isolato (venv) per le dipendenze del backend.
Vai nella cartella `Backend` e crea il venv:

```bash
cd Backend
python -m venv .venv
```

Il venv viene creato al primo setup e va rigenerato solo se cancellato.
La cartella `.venv/` non viene caricata su GitHub (è in `.gitignore`).

### Attivazione del venv

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows (cmd):

```bat
.\.venv\Scripts\activate.bat
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Dopo l'attivazione, il prompt mostrerà `(.venv)` e il comando `python` farà
riferimento all'interprete del venv.

### Installazione delle dipendenze

```bash
pip install -r requirements.txt
```

Installa Flask e tutte le dipendenze elencate in `requirements.txt`.
Quando installi un nuovo pacchetto, aggiorna il file con:

```bash
pip install <nuovo-pacchetto>
pip freeze > requirements.txt
```

### Avvio del server

```bash
python main.py
```

Il server parte su http://localhost:5000.

### Se vedi `ModuleNotFoundError: flask`

Probabilmente il venv non è stato creato o attivato: ripeti i passi di setup
sopra prima di avviare il server.
