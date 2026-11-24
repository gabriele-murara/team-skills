---
name: download-issue
description: Scarica una issue dal gestionale (Redmine, GitHub, GitLab) con descrizione, note o commenti e link agli allegati, e la salva in issues/issue-<numero>.md. Usala quando l'utente chiede di scaricare, leggere o aggiornare la copia locale di una issue.
argument-hint: "<numero-issue>"
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/download_issue.sh:*) Read Glob
---

# Download di una issue

Scarica la issue numero `$ARGUMENTS` dal gestionale e salvala in
`issues/issue-<numero>.md`, il file che legge la skill `open-issue`.

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

## Configurazione

Lo script `download_issue.sh` di questa skill legge le variabili
d'ambiente oppure, se mancano, le righe `CHIAVE=valore` del file
`.claude/.env.claude` del progetto (non versionato):

| `ISSUE_TRACKER` | Variabili |
|---|---|
| `redmine` | `REDMINE_URL`, `REDMINE_API_KEY` |
| `github` | nessuna: usa `gh`, autenticato con `gh auth login` |
| `gitlab` | `GITLAB_URL`, `GITLAB_TOKEN` (scope `read_api`); `GITLAB_PROJECT` (`gruppo/progetto` o id) solo se diverso dal remote `origin` |

Servono `curl` e `jq` (per GitHub `gh` e `jq`).

**Non leggere, stampare o copiare i token** (`REDMINE_API_KEY`,
`GITLAB_TOKEN`). Non aprire `.claude/.env.claude` con Read o `cat`: lo
legge lo script, che non mostra mai i token.

## 1. Controlli

`$ARGUMENTS` deve essere un numero intero positivo (eventuale `#`
iniziale ignorato). Se manca o non è valido, esci con errore:
`Uso: download-issue <numero-issue>`.

## 2. Download

Esegui dalla root del progetto (root del repository git, se esiste):

```bash
${CLAUDE_SKILL_DIR}/download_issue.sh <numero>
```

Lo script crea, se mancano, la cartella `issues/` e il suo `.gitignore`
(`*` e `!.gitignore`), e scrive il file con questa struttura:

```markdown
# #<numero> <titolo>

- **Fonte:** <redmine|github|gitlab> - <URL web della issue>
- **Tipo:** <tracker o etichette>
- **Stato:** <stato>
- **Priorità:** <priorità, solo Redmine>
- **Versione:** <fixed_version o milestone>
- **Autore:** <autore>
- **Assegnatario:** <assegnatari>
- **Scaricata il:** <data AAAA-MM-GG>

## Descrizione

## Allegati

## Note

### <autore> - <data>
```

Descrizione e note sono riportate così come sono, in ordine cronologico;
sono escluse le note vuote e quelle di sistema di GitLab. Gli allegati
non vengono scaricati: restano link al gestionale.

Esiti:

- **file scritto** o **già aggiornato** (contenuto uguale, a parte la
  data di download): prosegui al punto 3;
- **codice di uscita 3**: `issues/issue-<numero>.md` esiste già con un
  contenuto diverso e potrebbe contenere modifiche dell'utente. Chiedi
  all'utente se sovrascriverlo; se sì, rilancia con `--force` prima del
  numero;
- **errore**: riporta il messaggio all'utente e fermati. Casi tipici:
  - variabile mancante: indica quale impostare (nel blocco `env` di
    `.claude/settings.local.json` o in `.claude/.env.claude`);
  - connessione fallita o timeout: di solito la VPN non è attiva o
    l'URL è errato;
  - HTTP 401: credenziali non valide o scadute;
  - HTTP 403: credenziali senza accesso al progetto;
  - HTTP 404: numero della issue o progetto errati.

## 3. Riepilogo

Leggi `issues/issue-<numero>.md` con Read e indica all'utente:

- il percorso del file;
- un riassunto della richiesta e dei punti emersi nelle note.

Se la skill è stata richiamata da `open-issue`, prosegui con il passo
successivo di quella skill.
