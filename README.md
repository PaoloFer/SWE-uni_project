# Progetto Uni

## Struttura

- `Backend/` — API Flask
- `Frontend/` — applicazione client

## Backend (Flask)

### Prerequisiti

- [Python 3.10 o successivo](https://www.python.org/downloads/) installato
  (il progetto è stato verificato con Python 3.12).

Il nome del comando dipende dal sistema operativo e da come è stato installato
Python:

- Windows: `python`
- macOS/Linux: `python3`

Verifica versione e disponibilità dell'interprete prima di procedere.

Windows (PowerShell o prompt dei comandi):

```powershell
python --version
```

macOS/Linux:

```bash
python3 --version
```

L'output deve indicare una versione pari o successiva alla 3.10. Su Windows,
se `python` non è disponibile ma è installato il Python Launcher, è possibile
usare `py` come alternativa:

```powershell
py --version
```

`py` è quindi un fallback specifico di Windows, non un requisito del progetto.

### Setup del virtualenv

Il progetto usa un ambiente Python isolato (venv) per le dipendenze del backend.
Apri un terminale nella cartella principale del progetto ed entra in `Backend`:

```bash
cd Backend
```

Poi crea il virtualenv con il comando adatto al sistema operativo.

Windows:

```powershell
python -m venv .venv
```

macOS/Linux:

```bash
python3 -m venv .venv
```

Solo su Windows, se `python` non è riconosciuto ma `py --version` funziona,
crea il virtualenv con:

```powershell
py -m venv .venv
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

### Risoluzione dei problemi

Se su Windows `python` apre il Microsoft Store oppure non viene riconosciuto:

- verifica che Python sia installato da [python.org](https://www.python.org/downloads/);
- verifica che l'opzione per aggiungere Python al `PATH` sia abilitata;
- in alternativa, prova `py --version` e usa `py -m venv .venv`.

Se su Linux la creazione del virtualenv segnala che il modulo `venv` non è
disponibile, installa il pacchetto fornito dalla distribuzione, per esempio su
Ubuntu/Debian:

```bash
sudo apt install python3-venv
```

Dopo l'attivazione del virtualenv, su tutti i sistemi i comandi sono gli stessi:

```bash
python --version
python -m pip install -r requirements.txt
python main.py
```
