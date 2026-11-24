---
name: open-issue
description: Apre il lavoro su una issue - crea e pubblica il branch issue-<numero> da un branch develop o develop-*, legge il testo della issue dal gestionale (Redmine, GitHub, GitLab), ne salva una copia in issues/issue-<numero>.md, oppure lo legge dalla cartella issues, e propone una soluzione.
argument-hint: "<numero-issue>"
disable-model-invocation: true
---

# Apertura di una issue

Apri il lavoro sulla issue numero `$ARGUMENTS`.

## Gestionale: solo lettura

Sul gestionale (Redmine, GitHub, GitLab) l'agente può solo **leggere** le
issue. Non deve **mai** modificarle, nemmeno se l'utente lo chiede:

- niente creazione, modifica, chiusura, riapertura o eliminazione;
- niente commenti, note, allegati, tempo speso;
- niente cambi di stato, assegnatario, priorità, versione, etichette.

Usa solo richieste di lettura: `curl` senza `-X` né dati (quindi `GET`),
`gh issue view`, `gh issue list`. Mai `POST`, `PUT`, `PATCH`, `DELETE`, né
comandi come `gh issue create`, `edit`, `comment`, `close`, `reopen`,
`delete`. Se serve inserire un testo nel gestionale, scrivilo in un file
in `issues/`: lo copia l'utente.

## 1. Controlli

1. **Numero**: `$ARGUMENTS` deve essere un numero intero positivo
   (eventuale `#` iniziale ignorato). Se manca o non è valido, esci con
   errore: `Uso: open-issue <numero-issue>`.
2. **Repository**: deve essere un repository git
   (`git rev-parse --show-toplevel`), altrimenti esci con errore.
3. **Branch di partenza**: `git branch --show-current` deve essere
   `develop` oppure iniziare con `develop-`. Altrimenti esci con errore:
   `open-issue si esegue solo da develop o develop-*: branch attuale
   <branch>`. Non cambiare branch al posto dell'utente.
4. **Branch già esistente**: se esiste già `issue-<numero>` in locale
   (`git branch --list issue-<numero>`) o su `origin`
   (`git ls-remote --heads origin issue-<numero>`), esci con errore e
   indica dove esiste. Non sovrascriverlo e non farne il checkout.
5. **Modifiche non committate**: se `git status --porcelain` non è vuoto,
   avvisa l'utente che le modifiche passeranno nel nuovo branch e chiedi
   se procedere.

## 2. Creazione del branch

```bash
git checkout -b issue-<numero>
git config branch.issue-<numero>.base <branch-di-partenza>
git push origin issue-<numero> --set-upstream
```

Il valore `branch.issue-<numero>.base` registra il branch di partenza:
`close-issue` lo usa per confrontare le modifiche. Se il push fallisce,
riporta l'errore all'utente e fermati: il branch locale resta creato.

## 3. Testo della issue

Cerca il testo della issue in quest'ordine e fermati alla prima fonte
che lo restituisce.

### 3.1 Gestionale

Il gestionale è indicato dalla variabile d'ambiente `ISSUE_TRACKER`
(`redmine`, `github` o `gitlab`), di norma impostata nel blocco `env` di
`.claude/settings.json` del progetto, oppure nel file
`.claude/.env.claude`. Se non è impostata in nessuno dei due, salta al
punto 3.2.

Scarica la issue con lo script della skill `download-issue` (cartella
`../download-issue/` rispetto a questa skill), che salva la copia locale
in `issues/issue-<numero>.md`:

```bash
${CLAUDE_SKILL_DIR}/../download-issue/download_issue.sh <numero>
```

Le variabili richieste, il formato del file e il significato degli
errori sono descritti in `../download-issue/SKILL.md`. Non stampare mai
i token, non includerli nei messaggi all'utente e non aprire
`.claude/.env.claude`: lo legge lo script.

- **File scritto o già aggiornato**: leggi `issues/issue-<numero>.md` e
  vai al punto 4.
- **Codice di uscita 3**: il file esiste già con un contenuto diverso,
  che potrebbe contenere modifiche dell'utente. Chiedi se sovrascriverlo
  (rilancia con `--force` prima del numero) o se usare il file com'è.
- **Errore** (credenziali mancanti, connessione fallita, HTTP 4xx):
  riporta il messaggio all'utente e passa al punto 3.2. Una connessione
  fallita o in timeout indica di solito che la VPN non è attiva.

### 3.2 Cartella `issues`

Cerca in `issues/` (nella root del repository) i file `*.md` e `*.pdf`
il cui nome contiene il numero della issue come numero a sé: `123`
corrisponde in `123-login.md` e `issue_123.pdf`, ma non in `1234.md`.
Escludi `closed-issue-<numero>.md`, che è la nota di chiusura.

- Un solo file: leggilo.
- Più file: chiedi all'utente quale usare.
- Nessun file: vai al punto 3.3.

### 3.3 Nessun testo trovato

Dillo all'utente e chiedigli di descrivere la issue o di indicare dove
trovarla. Il branch resta creato.

## 4. Analisi e proposta

Con il testo della issue:

1. Riassumi la issue in poche righe: tipo, obiettivo, criteri di
   accettazione.
2. Analizza il codice coinvolto: leggi i file citati e cerca quelli
   collegati. Se il progetto ha un `CLAUDE.md`, rispetta le sue regole.
3. Se la issue è ambigua o incompleta, elenca le domande per l'utente.
4. Proponi la soluzione: approccio, file da creare o modificare,
   eventuali migrazioni, test da scrivere o aggiornare, rischi. Se ci
   sono alternative ragionevoli, indicale con i loro pro e contro e
   consiglia quella da preferire.

**Non modificare il codice**: aspetta che l'utente approvi la proposta.

## 5. Risposta all'utente

Indica:

- il branch creato, il branch di partenza e l'esito del push;
- la fonte del testo della issue (gestionale o file) e, se l'hai
  salvata, il percorso della copia locale;
- il riassunto, le eventuali domande e la soluzione proposta.
