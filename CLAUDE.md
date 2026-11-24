# CLAUDE.md

Questo repository è un **marketplace di plugin per Claude Code** (`team-skills`).
Non contiene codice applicativo da eseguire: contiene skill (file `SKILL.md`) e
file di riferimento che le skill copiano nei progetti di destinazione.
Il `README.md` è la documentazione per chi installa i plugin.

## Struttura

```
.claude-plugin/marketplace.json            elenco dei plugin, con versione
plugins/<plugin>/.claude-plugin/plugin.json manifest del plugin, con versione
plugins/<plugin>/skills/<skill>/SKILL.md    istruzioni della skill (frontmatter + corpo)
```

Plugin attuali:

- `issues` — skill `write-issue`, `download-issue`, `open-issue`,
  `close-issue`: preparano testi di issue in `issues/` e lavorano con
  Redmine, GitHub o GitLab (variabile `ISSUE_TRACKER`). `download-issue`
  contiene lo script `download_issue.sh`, l'unico punto che legge il
  gestionale.
- `laravel` — skill `laravel-setup`: prepara un progetto Laravel 11/12.
  Sui progetti legacy (Laravel < 11) scrive solo un `CLAUDE.md` con alcune
  sezioni delle regole (sezione 7 di `SKILL.md`) e non tocca altro. Gli
  altri file della cartella (`LARAVEL_CODING_RULES.md`, `bootstrap/`,
  `logger/`, `helpers/`) sono **modelli copiati nel progetto di
  destinazione**, non codice di questo repository.
- `django` — skill `django-setup`: prepara un progetto Django 4.2/5.x/6.x,
  con la stessa struttura di `laravel-setup`. Sui progetti legacy (Django
  < 4.2) scrive solo un `CLAUDE.md` con alcune sezioni delle regole
  (sezione 7 di `SKILL.md`) e non tocca altro. Python sempre >= 3.9. Anche qui
  `DJANGO_CODING_RULES.md`, `core/`, `logger/` e `helpers/` sono modelli
  per il progetto di destinazione.

## Regole per le modifiche

### Versioni

Ogni modifica a un plugin richiede un aumento di versione, altrimenti chi lo ha
installato continua a usare la copia in cache.

- Aggiorna la `version` in `plugins/<plugin>/.claude-plugin/plugin.json` **e**
  nella voce del plugin in `.claude-plugin/marketplace.json`: devono coincidere.
- Semver: **major** per modifiche incompatibili (skill rinominata o rimossa,
  argomento o variabile d'ambiente cambiati); **minor** per funzionalità
  compatibili (skill nuova, nuovo gestionale, metadati); **patch** per
  correzioni che non cambiano il comportamento previsto.

### Verifica

Dopo ogni modifica ai manifest o alle skill:

```bash
claude plugin validate .
```

Non ci sono test né build.

### README

Se aggiungi, rinomini o cambi l'uso di una skill, o cambi variabili d'ambiente
e configurazione, aggiorna anche `README.md` (tabella dei plugin, sezione sul
gestionale).

## Convenzioni delle skill

- **Lingua**: le skill del plugin `issues` e il `README.md` sono in italiano;
  le skill `laravel-setup` e `django-setup` e i loro file di riferimento
  sono in inglese.
  Mantieni la lingua del file che modifichi. Niente emoji.
- **Frontmatter**: `name` (uguale al nome della cartella), `description`
  (dice cosa fa e quando usarla, perché guida l'invocazione automatica),
  `argument-hint`; dove serve `disable-model-invocation` e `allowed-tools`.
  Gli argomenti arrivano in `$ARGUMENTS`.
- **Percorsi** nei file di una skill: relativi alla cartella della skill
  (ad esempio `logger/SETUP_LOGGER.md`).
- Le skill invocate dall'utente si chiamano con il prefisso del plugin:
  `/issues:open-issue 123`, `/laravel:laravel-setup`.

### Plugin `issues`

- La sezione **"Gestionale: solo lettura"** è ripetuta identica nelle
  quattro skill: se la cambi, cambiala in tutte. Le skill non devono mai scrivere sul
  gestionale (solo `GET`, `gh issue view`/`list`); i testi da inserire vanno in
  file sotto `issues/`.
- La cartella `issues/` del progetto di destinazione ha un `.gitignore` con
  `*` e `!.gitignore`.
- Le skill sono collegate: `open-issue` crea il branch `issue-<n>` da
  `develop`/`develop-*` e registra il branch di partenza in
  `git config branch.issue-<n>.base`, che `close-issue` legge; `open-issue`
  scarica la issue con `../download-issue/download_issue.sh`, che scrive
  `issues/issue-<n>.md` (codice di uscita 3 se il file esiste con un
  contenuto diverso), e altrimenti cerca in `issues/` i file con il
  numero della issue nel nome, come quelli prodotti da `write-issue` e
  rinominati dall'utente. Se cambi uno di questi
  accordi, aggiorna tutte le skill coinvolte.
- I token (`REDMINE_API_KEY`, `GITLAB_TOKEN`) non devono mai comparire
  nell'output né nei file scritti. Lo script li legge dall'ambiente o da
  `.claude/.env.claude` e li passa a `curl` come header, mai sulla riga
  di comando. Dopo una modifica allo script provalo con i tre gestionali
  (anche con `curl` e `gh` finti) e controlla `bash -n`.

### Plugin `laravel`

- `LARAVEL_CODING_RULES.md` diventa il `CLAUDE.md` del progetto Laravel:
  **non** sono regole per questo repository.
- `SKILL.md` e `logger/SETUP_LOGGER.md` fanno riferimento alle sezioni di
  `LARAVEL_CODING_RULES.md` per numero (ad esempio "section 5.2") e ai file
  in `helpers/`, `logger/`, `bootstrap/`. Se rinumeri una sezione o rinomini
  un file, aggiorna i riferimenti.
- I file PHP sono modelli: `bootstrap/constants.php` contiene i segnaposto
  `__APP_NAME__` e `__VERSION__`, sostituiti durante il setup.
- Il `CLAUDE.md` legacy copia il Glossario e le sezioni 1, 2.1, 2.2, 2.3,
  2.4, 3.1, 3.2, 3.3, 4, 5.6, 6.1 e 7 di `LARAVEL_CODING_RULES.md`, come per Django:
  queste sezioni non devono citare gli helper (Logger, `BaseModel`,
  `BulkInsert`, `bootstrap/constants.php`) né rimandare a sezioni escluse.
  Se rinumeri o sposti sezioni, aggiorna la tabella della sezione 7.1 di
  `SKILL.md`.

### Plugin `django`

- Valgono le stesse indicazioni del plugin `laravel`:
  `DJANGO_CODING_RULES.md` diventa il `CLAUDE.md` del progetto Django,
  `SKILL.md` e `logger/SETUP_LOGGER.md` ne citano le sezioni per numero, e
  `core/constants.py` contiene il segnaposto `__APP_NAME__`.
- I progetti Django seguono la struttura a package della sezione 5.6 delle
  regole (`<prefix>_models`, `<prefix>_utils`, ..., una classe per
  modulo), e così gli helper: `helpers/base_model.py`,
  `helpers/base_model_with_activity_log.py`, `helpers/soft_deletes.py`,
  `helpers/bulk_insert.py` e
  `logger/logger.py` vanno in `core/<prefix>_models/` e
  `core/<prefix>_utils/`. I file che importano altri helper contengono il
  segnaposto `__PREFIX__`; `core/apps.py`, `core/version.py` e
  `core/constants.py` restano nella root dell'app.
- Nei progetti Django la versione sta solo nel file `.version` della root,
  letto da `core.version.get_version()`; `core.constants.VERSION` e
  `settings.VERSION` derivano da lì. In `laravel-setup` la versione è la
  costante `VERSION` di `bootstrap/constants.php`: la differenza è per
  scelta e non va uniformata.
- Il `CLAUDE.md` legacy copia il Glossario e le sezioni 1, 2.1, 2.2, 2.3,
  2.4, 3.1, 3.2, 3.3, 4, 5.6, 6.1 e 7 di
  `DJANGO_CODING_RULES.md`: queste sezioni non devono citare gli helper
  (Logger, `core`, `.version`) né rimandare a sezioni escluse. Se
  rinumeri o sposti sezioni, aggiorna la tabella della sezione 7.1 di
  `SKILL.md`.
- Le due skill sono parallele: le sezioni di `DJANGO_CODING_RULES.md` hanno
  la stessa numerazione di `LARAVEL_CODING_RULES.md` (le sezioni che
  esistono solo in Django, come la 5.4, vengono dopo quelle comuni,
  per questo `LARAVEL_CODING_RULES.md` passa da 5.3 a 5.5). La sezione 5.6
  (struttura del codice) è diversa per scelta: in Django la struttura a
  package `<prefix>_<kind>`, in Laravel la struttura standard del
  framework, con una classe dedicata per ogni helper o attività di
  business.
  Anche il Glossario e la regola sull'activity log per ogni entity
  (sezione 5.1) sono uguali nelle due regole, tranne la definizione di
  entity, che è diversa per scelta e non va uniformata: in Laravel
  model + view + controller, in Django model + view + serializer. Se
  cambi una regola
  che non dipende dal framework (metodo di lavoro, git, migrazioni), valuta
  se va cambiata anche nell'altra.
- I file Python seguono le regole che impongono ai progetti: 80 colonne,
  `str.format()`. Prima di pubblicarli provali su un progetto Django di
  prova fuori dal repository (`startproject`, `startapp core`, copia dei
  file, `check`, Logger, auditlog, `BulkInsert`).
