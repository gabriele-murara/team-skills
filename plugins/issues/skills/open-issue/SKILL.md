---
name: open-issue
description: Apre il lavoro su una issue - crea e pubblica il branch issue-<numero> da un branch develop o develop-*, legge il testo della issue dal gestionale (Redmine, GitHub, GitLab) o dalla cartella issues e propone una soluzione.
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
`.claude/settings.json` del progetto. Se non è impostata, salta al
punto 3.2.

Non stampare mai i token né includerli nei messaggi all'utente.

- **redmine**: servono `REDMINE_URL` e `REDMINE_API_KEY`.

  ```bash
  curl -sf -H "X-Redmine-API-Key: $REDMINE_API_KEY" \
      "$REDMINE_URL/issues/<numero>.json?include=journals,attachments"
  ```

  Usa `subject`, `description`, `tracker`, `status`, `priority`,
  `fixed_version` e le note dei `journals`.

- **github**: serve `gh` autenticato (`gh auth status`).

  ```bash
  gh issue view <numero> --json number,title,body,labels,milestone,comments
  ```

- **gitlab**: servono `GITLAB_URL` (ad esempio `https://gitlab.com`) e
  `GITLAB_TOKEN`. Ricava il percorso del progetto (`gruppo/progetto`) da
  `git remote get-url origin` e codificalo per l'URL (`/` → `%2F`).

  ```bash
  curl -sf -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
      "$GITLAB_URL/api/v4/projects/<percorso-codificato>/issues/<numero>"
  curl -sf -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
      "$GITLAB_URL/api/v4/projects/<percorso-codificato>/issues/<numero>/notes?sort=asc"
  ```

Se le credenziali mancano o la chiamata fallisce, dillo all'utente
(senza mostrare i token) e passa al punto 3.2.

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
- la fonte del testo della issue (gestionale o file);
- il riassunto, le eventuali domande e la soluzione proposta.
