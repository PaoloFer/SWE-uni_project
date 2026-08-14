# Utenti di test

Credenziali temporanee per provare l'interfaccia. Sono definite per il solo
ambiente di sviluppo/test e vengono salvate **hashate** in
`Backend/data/users.csv`.

## Credenziali

| Username   | Password   | Ruolo   | Entity ID | Destinazione login |
|------------|------------|---------|-----------|--------------------|
| `mrossi`   | `password` | doctor  | M1        | `/doctor/`         |
| `fgiacomi` | `password` | patient | 1         | `/patient/`        |
| `admin`    | `admin`    | system  | SYSTEM1   | `/system/`         |

## Come testare

1. Avvia il server (dalla cartella `Backend`):

   ```bash
   python main.py
   ```

2. Apri `http://localhost:5000/` → verrai reindirizzato alla pagina di login.
3. Inserisci una delle coppie username/password sopra.

## Nota

- Dopo il login si viene reindirizzati alla dashboard del proprio ruolo:
  - **doctor** → gestione pazienti, terapie, info cliniche, notifiche
  - **patient** → area paziente (placeholder)
  - **system** → inserimento dati iniziali (placeholder)
- Le altre aree sono protette: un utente non può accedere a dashboard di
  ruoli diversi.
- Queste credenziali NON sono adatte alla produzione. In produzione
  l'inserimento degli utenti dovrebbe avvenire tramite l'area responsabili
  (UC-R1) e le password dovrebbero essere gestite con criteri adeguati.