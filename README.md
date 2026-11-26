# team-skills

Marketplace di plugin per Claude Code con le skill condivise tra i progetti.

| Plugin | Skill | Uso |
|---|---|---|
| `laravel` | `laravel-setup` | Setup di un progetto Laravel 11/12: `CLAUDE.md`, costanti, Logger, classi helper. Sui progetti legacy (Laravel < 11) scrive solo le regole in `CLAUDE.md` |
| `django` | `django-setup` | Setup di un progetto Django 4.2/5.x/6.x: `CLAUDE.md` (con la struttura a package, una classe per modulo), app `core` con versione in `.version`, Logger, classi helper. Sui progetti legacy (Django < 4.2) scrive solo le regole in `CLAUDE.md` |
| `django` | `django-apm` | Aggiunge Elastic APM a un progetto Django: agente `elastic-apm` 6.x configurato da variabili d'ambiente e spento di default, tracciamento facoltativo dei processi senza HTTP, comando `check_apm`, test e guida `APM_CONFIGURATION.md` |
| `issues` | `write-issue` | Scrive il testo di una issue in `issues/`, da copiare nel gestionale |
| `issues` | `download-issue <n>` | Scarica la issue dal gestionale in `issues/issue-<n>.md` |
| `issues` | `open-issue <n>` | Da `develop`/`develop-*`: crea e pubblica `issue-<n>`, legge la issue e propone una soluzione |
| `issues` | `close-issue <n>` | Scrive la nota di chiusura in `issues/closed-issue-<n>.md` |

Le skill dei plugin si invocano con il nome del plugin come prefisso, ad
esempio `/issues:open-issue 123` o `/laravel:laravel-setup`.

## Installazione in un progetto

Aggiungi a `.claude/settings.json` del progetto (va nel repository del
progetto, così vale per tutti):

```json
{
  "extraKnownMarketplaces": {
    "team-skills": {
      "source": { "source": "github", "repo": "gabriele-murara/team-skills" }
    }
  },
  "enabledPlugins": {
    "issues@team-skills": true,
    "laravel@team-skills": true,
    "django@team-skills": true
  },
  "env": {
    "ISSUE_TRACKER": "redmine",
    "REDMINE_URL": "https://redmine.example.com"
  }
}
```

Abilita solo i plugin che servono al progetto (`laravel` solo nei
progetti Laravel, `django` solo nei progetti Django). All'apertura del progetto Claude Code chiede di
fidarsi del marketplace e installa i plugin.

In alternativa, a mano: `/plugin marketplace add gabriele-murara/team-skills`, poi
`/plugin install issues@team-skills`.

Per aggiornare le skill: `/plugin marketplace update team-skills`.

## Configurazione del gestionale

Le skill `issues` accedono al gestionale **solo in lettura**: non creano,
modificano, commentano o chiudono mai le issue. I testi da inserire nel
gestionale vengono scritti in `issues/` e li copia l'utente.

`download-issue` (usata anche da `open-issue`) legge la issue dal
gestionale indicato da `ISSUE_TRACKER` e ne salva una copia in
`issues/issue-<n>.md`, con descrizione, note o commenti e link agli
allegati. Richiede `curl` e `jq`. Se la variabile non è impostata, o mancano le credenziali, cerca il testo
in un file `*.md` o `*.pdf` della cartella `issues/` che ha il numero
della issue nel nome.

| `ISSUE_TRACKER` | Variabili | Note |
|---|---|---|
| `redmine` | `REDMINE_URL`, `REDMINE_API_KEY` | Chiave API dal profilo utente Redmine |
| `github` | — | Usa `gh`, autenticato con `gh auth login` |
| `gitlab` | `GITLAB_URL`, `GITLAB_TOKEN`, `GITLAB_PROJECT` (facoltativa) | Token personale con scope `read_api`; il progetto si ricava dal remote `origin`, `GITLAB_PROJECT` (`gruppo/progetto` o id) serve solo se è diverso |

I token non vanno in `.claude/settings.json`: mettili nel blocco `env` di
`.claude/settings.local.json` del progetto (non versionato), nel profilo
della shell o nel file `.claude/.env.claude` del progetto, con righe
`CHIAVE=valore`. Il file `.claude/.env.claude` va escluso da git; lo
legge solo lo script di `download-issue`, così i token non passano
dall'agente. Le variabili d'ambiente hanno la precedenza sul file.

```dotenv
# .claude/.env.claude
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=glpat-...
```

## Cartella `issues`

Le skill `issues` scrivono in `issues/` nella root del progetto. La
cartella contiene un `.gitignore` che esclude tutto tranne se stesso, così
i testi delle issue restano locali.

## Struttura del repository

```
.claude-plugin/marketplace.json     elenco dei plugin
plugins/<plugin>/.claude-plugin/plugin.json
plugins/<plugin>/skills/<skill>/SKILL.md
```

Per aggiungere una skill: crea la sua cartella in `plugins/<plugin>/skills/`,
aumenta `version` in `plugin.json` e nella voce di `marketplace.json`,
poi verifica con `claude plugin validate .`.

## Versioni

Le versioni seguono il formato `major.minor.patch`:

- **major**: modifiche incompatibili (ad esempio una skill rinominata o
  rimossa, un argomento o una variabile d'ambiente cambiati);
- **minor**: funzionalità nuove e compatibili (una skill nuova, un nuovo
  gestionale supportato, metadati come la licenza);
- **patch**: correzioni che non cambiano il comportamento previsto.

La versione in `plugin.json` e quella nella voce del plugin in
`marketplace.json` devono coincidere. Senza un aumento di versione chi ha
già installato il plugin continua a usare la copia in cache.
