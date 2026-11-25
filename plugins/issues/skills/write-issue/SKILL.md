---
name: write-issue
description: Scrive il testo di una issue (bug, funzionalità o attività) in un file CommonMark nella cartella issues del progetto, pronto da copiare nel gestionale (Redmine, GitHub, GitLab). Usala quando l'utente descrive un problema da risolvere o un'attività da svolgere e vuole preparare la issue.
argument-hint: "[descrizione del problema o dell'attività]"
---

# Scrittura di una issue

Prepara il testo di una issue a partire da quanto descritto dall'utente
(`$ARGUMENTS` e la conversazione). L'utente copierà il testo nel
gestionale, dove creerà la issue e le darà assegnatario, priorità,
versione ecc. Questa skill **non** crea la issue sul gestionale.

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

## 1. Cartella `issues`

Nella root del progetto (root del repository git, se esiste) deve
esistere la cartella `issues/` con un `.gitignore` che ignora tutto il
contenuto tranne se stesso:

```gitignore
*
!.gitignore
```

Se la cartella o il `.gitignore` mancano, creali. Se il `.gitignore`
esiste con un contenuto diverso, non modificarlo: segnalalo all'utente.

## 2. Raccolta e verifica delle informazioni

1. Classifica la richiesta: **bug**, **funzionalità** o **attività**
   (manutenzione, aggiornamento, refactoring, documentazione...).
2. Verifica quanto descritto sul codice del progetto: cerca i file, le
   classi, le rotte, le tabelle e i comportamenti citati, e controlla che
   esistano e funzionino come descritto. Annota i file coinvolti.
3. Individua le informazioni mancanti o ambigue, ad esempio:
   - bug: passi per riprodurlo, comportamento atteso e attuale, ambiente
     (produzione, staging, locale), messaggi di errore o log;
   - funzionalità: chi la usa, cosa deve poter fare, casi limite, vincoli;
   - per tutte: criteri per considerare la issue risolta.
4. Se manca qualcosa di necessario, o se il codice non corrisponde a
   quanto descritto, chiedi all'utente prima di scrivere. Fai le domande
   tutte insieme e solo su ciò che serve davvero.

Non proporre e non implementare la soluzione: la issue descrive il
problema e il risultato atteso. Le note tecniche servono solo a
orientare chi ci lavorerà.

## 3. Scrittura del file

Scrivi il file `issues/<AAAA-MM-GG>-<slug>.md`, dove `slug` è il titolo
in minuscolo, con parole separate da `-` e senza caratteri speciali
(massimo 50 caratteri). Se il file esiste già, aggiungi un suffisso
`-2`, `-3`...

Struttura del file:

```markdown
# <Titolo breve e specifico>

## Contesto

[Dove si colloca il problema o l'attività, e perché è necessario.]

## Descrizione

[Bug: comportamento attuale. Funzionalità/attività: cosa va fatto.]

## Passi per riprodurre

1. [...]

## Comportamento atteso

[...]

## Criteri di accettazione

- [ ] [Condizione verificabile]

## Note tecniche

- `percorso/del/file` — [perché è rilevante]

## Riferimenti

- [Link, issue collegate, log, screenshot]
```

Regole:

- **Passi per riprodurre** solo per i bug; **Comportamento atteso** per
  bug e funzionalità. Ometti **Note tecniche** e **Riferimenti** se
  vuote.
- La riga `# Titolo` va nel campo titolo del gestionale; il resto, dai
  titoli `##` in giù, va nella descrizione.
- Formato CommonMark; codice e log in code block con il linguaggio.
- Nessun limite di lunghezza delle righe (il limite di 80 colonne non
  vale per i file `.md`): non andare a capo dentro un paragrafo o una
  voce di elenco, scrivili su una sola riga.
- Lingua: italiano. Niente emoji.
- Testo conciso e comprensibile a chi non ha seguito la conversazione:
  niente riferimenti a "come detto sopra" o alla sessione.

## 4. Risposta all'utente

Indica:

- il percorso del file creato;
- il titolo proposto e il tipo (bug, funzionalità, attività);
- che, dopo aver creato la issue sul gestionale, conviene rinominare il
  file includendo il numero della issue (ad esempio
  `issues/123-<slug>.md`): così `open-issue 123` lo trova anche senza
  accesso al gestionale.
