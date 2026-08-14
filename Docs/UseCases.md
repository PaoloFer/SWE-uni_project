# Use Case — Sistema di Telemedicina per Diabetici di Tipo 2

Gli use case sono suddivisi per attore primario. Gli alert/notifiche vengono
modellati in due parti: il **sistema** genera e scrive le notifiche (push,
verso un inbox/bacheca), mentre medico e paziente hanno propri use case attivi
di **consultazione** delle notifiche pendenti (pull).

## Attore: Paziente (previo autenticazione)

- **UC-P1 – Inserire rilevazione di glicemia**
  Registra il valore di glicemia misurato prima e dopo ogni pasto, con data, ora
  e momento del pasto. È il dato principale di monitoraggio del paziente.

- **UC-P2 – Aggiungere sintomo**
  Registra un sintomo percepito (spossatezza, nausea, mal di testa, ecc.).

- **UC-P3 – Registrare assunzione di farmaco/insulina**
  Registra giorno, ora, farmaco e quantità assunta, in coerenza con la terapia
  prescritta dal diabetologo.

- **UC-P4 – Segnalare sintomi, patologie e/o terapie concomitanti**
  Fornisce informazioni su sintomi, patologie o terapie aggiuntive, indicando il
  periodo associato.

- **UC-P5 – Contattare il medico di riferimento**
  Invia email al proprio medico di riferimento per richieste e domande varie.

- **UC-P6 – Consultare le proprie notifiche**
  Legge dall'inbox gli alert a lui rivolti: promemoria di assunzione dimenticata
  e inviti a completare gli inserimenti relativi alle assunzioni.

## Attore: Diabetologo (previo autenticazione)

- **UC-M1 – Prescrivere una terapia**
  Specifica il farmaco, il numero di assunzioni giornaliere, la quantità per
  ogni assunzione ed eventuali indicazioni (dopo i pasti, lontano dai pasti, ecc.).

- **UC-M2 – Modificare una terapia**
  Aggiunge o modifica la terapia di un paziente in base all'evoluzione del suo
  stato clinico.

- **UC-M3 – Visualizzare i dati di un paziente**
  Consulta i dati clinici di ogni paziente (glicemie, assunzioni, sintomi,
  terapie, informazioni cliniche).

- **UC-M4 – Visualizzare dati in forma sintetica**
  Consulta gli andamenti della glicemia in forma aggregata, ad es. settimana per
  settimana o mese per mese.

- **UC-M5 – Aggiornare informazioni cliniche del paziente**
  Gestisce la sezione informativa del paziente: fattori di rischio (fumatore,
  ex-fumatore, dipendenze da alcol o stupefacenti, obesità), pregresse
  patologie e comorbidità presenti (es. ipertensione).

- **UC-M6 – Consultare le proprie notifiche / alert**
  Legge dall'inbox le segnalazioni a suo nome: pazienti non aderenti alle
  prescrizioni da più di 3 giorni consecutivi e glicemie oltre soglia, con
  modalità diverse a seconda della gravità.

## Attore: Responsabile del servizio

- **UC-R1 – Inserire dati iniziali di pazienti e medici**
  Inserisce i dati anagrafici e le credenziali necessarie all'autenticazione di
  pazienti e medici. Gestisce inoltre la relazione paziente–medico: ogni
  paziente ha esattamente un medico di riferimento e ogni medico può avere da
  0 a n pazienti. La relazione è persistita in `Backend/data/associations.csv`.

## Attore: Sistema (azioni automatiche)

- **UC-S1 – Autenticare utente**
  Verifica le credenziali e concede l'accesso a paziente o medico.

- **UC-S2 – Verificare coerenza delle assunzioni con le terapie prescritte**
  Controlla che le assunzioni registrate dai pazienti corrispondano a quanto
  prescritto (farmaco, quantità, frequenza).

- **UC-S3 – Sollecitare l'inserimento delle assunzioni**
  Invita il paziente a completare gli inserimenti relativi alle assunzioni di
  farmaci non ancora registrati.

- **UC-S4 – Generare alert verso il paziente**
  Scrive nell'inbox del paziente una notifica in caso di assunzione dimenticata.

- **UC-S5 – Generare alert verso il medico (mancata aderenza)**
  Scrive nell'inbox del medico una notifica se un paziente non segue le
  prescrizioni per più di 3 giorni consecutivi.

- **UC-S6 – Segnalare glicemie oltre soglia**
  Analizza le glicemie registrate e scrive nell'inbox del medico la segnalazione
  dei pazienti con valori oltre le soglie (pre-pasto 80–130 mg/dL, post-pasto
  ≤ 180 mg/dL), con modalità diverse in base alla gravità.

- **UC-S7 – Tracciare le operazioni dei medici**
  Registra quale medico ha effettuato ciascuna operazione, per la tracciabilità
  delle modifiche.