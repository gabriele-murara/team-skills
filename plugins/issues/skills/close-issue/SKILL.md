---
name: close-issue
description: Genera la nota di aggiornamento strutturata per chiudere una issue (Redmine, GitHub, GitLab), da copiare nel gestionale.
disable-model-invocation: false
argument-hint: "<numero-issue>"
allowed-tools: Bash(git diff:*) Bash(git log:*) Bash(git config:*) Bash(git branch:*) Write Read Glob Grep
---

# Chiusura issue

Genera una nota di aggiornamento strutturata per la issue #$ARGUMENTS.

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

## Istruzioni

1. **Raccogli informazioni dal contesto della conversazione**
   - Analizza il lavoro svolto durante la sessione corrente
   - Identifica i file modificati, aggiunti o rimossi
   - Identifica eventuali modifiche alla configurazione (variabili d'ambiente, settings)
   - Identifica eventuali breaking changes
   - Identifica eventuali note per il deploy

2. **Se necessario, integra con git**
   - Branch base: il valore di `git config branch.issue-$ARGUMENTS.base`,
     registrato da `open-issue`. Se manca, chiedi all'utente da quale
     branch `develop` o `develop-*` è partita la issue
   - Usa `git diff <base>...HEAD` per vedere tutte le modifiche del branch
   - Usa `git log <base>..HEAD --oneline` per vedere i commit

3. **Genera il file markdown**
   - Se mancano, crea la cartella `issues/` e il suo `.gitignore`
     (contenuto: `*` e `!.gitignore`, uno per riga)
   - Scrivi il file in: `issues/closed-issue-$ARGUMENTS.md`
   - Usa il template seguente

4. **Conferma** il percorso del file generato

## Template della nota

Il file deve seguire questo formato (CommonMark, titoli da ##):

```markdown
## Riassunto

[Breve descrizione di quanto fatto e del problema risolto/feature implementata]

## Implementazione

[Spiegazione tecnica di come e' stata fatta l'implementazione, le scelte architetturali e le motivazioni]

## Modifiche al codice

**File:** `[percorso/del/file]`

### Parti aggiunte

[Elenco numerato delle parti aggiunte, con snippet di codice se rilevanti]

```[linguaggio]
[codice aggiunto]
```

### Parti modificate

[Descrizione delle modifiche, oppure "Nessuna."]

### Parti rimosse

[Descrizione delle parti rimosse, oppure "Nessuna."]

## Modifiche alla configurazione

[Descrizione delle variabili d'ambiente aggiunte/modificate, oppure "Nessuna nuova variabile d'ambiente."]

| Variabile | Descrizione | Default | Obbligatoria |
|-----------|-------------|---------|--------------|
| NOME_VAR  | Descrizione | valore  | Si/No        |

## Breaking changes

[Descrizione dei breaking changes, oppure "Nessuno."]

## Note per il deploy

[Elenco puntato delle azioni richieste durante il deploy, oppure "Nessuna azione richiesta."]
```

## Specifiche di formattazione

- Formato: CommonMark
- Titoli: partire da ## (il livello # e' riservato al titolo della issue sul gestionale)
- Codice: formattare come code block con sintassi appropriata
- Lingua: italiano
- Non usare emoji
