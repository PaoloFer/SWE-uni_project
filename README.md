# Progetto Uni

## Struttura

- `Backend/` — API Flask
- `Frontend/` — applicazione client

## Backend (Flask)

### Prerequisiti

- [Python 3.12](https://www.python.org/downloads/) installato.

Il comando che avvia Python dipende dal sistema operativo:

- Windows: `py -3.12`
- macOS/Linux: `python3`

Verifica l'installazione con uno dei seguenti comandi.

Windows:

```powershell
py -3.12 --version
```

macOS/Linux:

```bash
python3 --version
```

L'output deve indicare Python 3.12. Nei comandi successivi viene usato il
comando appropriato per ciascun sistema operativo.

### Setup del virtualenv

Il progetto usa un ambiente Python isolato (venv) per le dipendenze del backend.
Apri un terminale nella cartella principale del progetto ed entra in `Backend`:

```bash
cd Backend
```

Poi crea il virtualenv con il comando adatto al sistema operativo.

Windows:

```powershell
py -3.12 -m venv .venv
```

macOS/Linux:

```bash
python3 -m venv .venv
```

Il virtualenv viene creato solo durante il primo setup e va rigenerato se la
cartella `.venv` viene cancellata. La cartella contiene file locali e non deve
essere aggiunta al repository.

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
python -m pip install -r requirements.txt
```

Installa Flask e tutte le dipendenze elencate in `requirements.txt`.
Quando installi un nuovo pacchetto, aggiorna il file con:

```bash
python -m pip install <nuovo-pacchetto>
python -m pip freeze > requirements.txt
```

### Avvio del server

```bash
python main.py
```

Il server parte su http://localhost:5000.

### Se vedi `ModuleNotFoundError: flask`

Probabilmente il venv non è stato creato o attivato: ripeti i passi di setup
sopra prima di avviare il server.

### Riepilogo dei comandi Python

Prima di attivare il virtualenv:

| Sistema operativo | Comando |
|-------------------|---------|
| Windows | `py -3.12` |
| macOS/Linux | `python3` |

Dopo aver attivato il virtualenv, su tutti i sistemi si usa:

```bash
python
```
