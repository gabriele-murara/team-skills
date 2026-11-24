---
name: django-setup
description: Sets up a Django project with the coding rules (CLAUDE.md, including the package layout with one class per module), the core app with the constants, the project Logger and the helper classes. Creates a new Django project, or completes an existing Django 4.2/5.x/6.x project by adding only the missing parts. On legacy projects (Django older than 4.2) it writes only the coding rules in CLAUDE.md and leaves the project as it is. Use it when the user asks to prepare, create, set up or align a Django project.
argument-hint: "[project-path]"
---

# Django project setup

Set up the Django project in `$ARGUMENTS` with the rules and the classes
in this skill folder:

- **new project**: the folder does not exist or is empty. Create a
  Django project with the latest Django release, then set it up;
- **existing project**: the folder contains a Django 4.2, 5.x or 6.x
  project. Add only the missing parts and do not touch the parts that
  already meet the rules;
- **legacy project**: the folder contains a project with Django older
  than 4.2. Write only the coding rules in `CLAUDE.md` (section 7): the
  rest of the project stays as it is.

Files of this skill (paths relative to this `SKILL.md`):

| File | Use |
|---|---|
| `DJANGO_CODING_RULES.md` | Becomes the `CLAUDE.md` of the project |
| `core/apps.py` | `core/apps.py` (registers the activity log models) |
| `core/version.py` | `core/version.py` (`get_version()`, reads `.version`) |
| `core/constants.py` | `core/constants.py` (`APP_NAME`, `VERSION`) |
| `logger/` | `logger.py` (→ `core/<prefix>_utils/logger.py`) and `SETUP_LOGGER.md` |
| `helpers/base_model.py` | `core/<prefix>_models/base_model.py` (`BaseModel`) |
| `helpers/base_model_with_activity_log.py` | `core/<prefix>_models/base_model_with_activity_log.py` (`BaseModelWithActivityLog`) |
| `helpers/soft_deletes.py` | `core/<prefix>_models/soft_deletes.py` (`SoftDeletes`) |
| `helpers/bulk_insert.py` | `core/<prefix>_utils/bulk_insert.py` (`BulkInsert`) |

`<prefix>` is the prefix of the packages of the project (section 3).
The helpers follow the package layout of `DJANGO_CODING_RULES.md`,
section 5.6: one class per module, in packages named `<prefix>_<kind>`
with an empty `__init__.py`. When copying a file, replace `__PREFIX__`
with the prefix.

Read `DJANGO_CODING_RULES.md` before starting: its rules apply to this
setup too. In particular: never apply migrations, never commit, never
write on the `main` branch, change only what is needed.

---

## 1. Mode and checks

1. **Target folder**: `$ARGUMENTS`. If it is empty, ask the user for the
   path of the project.
   - The folder does not exist or is empty → **new project**.
   - The folder contains `manage.py` and the project depends on Django
     (`requirements*.txt`, `pyproject.toml`, `Pipfile`, or Django
     installed in its environment) → **existing project**.
   - Anything else → stop and ask the user.
2. **Python** (new project): Python >= 3.9 (`python3 --version`), the
   `venv` module (`python3 -m venv --help`) and SQLite
   (`python3 -c "import sqlite3"`). If one is missing, stop and tell the
   user. pip installs the latest Django release that the Python version
   supports (Django 5.x needs Python >= 3.10, 6.x needs >= 3.12): with
   Python 3.9 it is Django 4.2, which no longer receives security fixes,
   so tell the user and ask whether to proceed.

Existing and legacy project (point 6 only for an existing project):

3. **Environment**: find how the project runs (DJANGO_CODING_RULES.md,
   section 3.1): the section "Execution environment" of an existing
   `CLAUDE.md`, a virtualenv in the project (`.venv/`, `venv/`), the
   active `VIRTUAL_ENV`, `uv` / `poetry`, or a Docker container
   (`Dockerfile` and `docker-compose.yml` / `compose.yaml`). Also find
   the dependency file and the settings module (`DJANGO_SETTINGS_MODULE`
   in `manage.py`; with split settings, the base module). If you cannot
   tell, ask the user how they run the project. Every command from here
   on runs in that environment, and it is written in `CLAUDE.md`
   (component A, or section 7.2 for a legacy project). Its Python must be >= 3.9
   (`python --version`): otherwise stop and tell the user.
4. **Django version**: `python -m django --version`. If Django is not
   installed in the environment, ask the user to install the
   dependencies first.
   - 4.2, 5.x, 6.x → **existing project**. Django 4.2 no longer receives
     security fixes: do not upgrade Django, and mention it in the report.
   - Older than 4.2 → **legacy project**: do point 5, then go to
     section 7.
   - Newer than 6.x → stop and tell the user.
5. **Git**: if the folder is a git repository, check the branch
   (`git branch --show-current`). On `main`, stop and ask the user to
   switch branch. If there are uncommitted changes (`git status`), tell
   the user and ask whether to proceed, so that the setup changes can be
   reviewed apart.
6. **Tests baseline**: run `python manage.py check` and the tests
   (`python manage.py test`, or `pytest` with `pytest-django`) and keep
   the results. They are compared with the results after the setup
   (section 5): failures that were already there are not caused by the
   setup. If the test database cannot be created (e.g. the database user
   cannot create databases), tell the user and go on without the
   baseline.

---

## 2. Create the project (new project only)

Ask the user the name of the settings package, proposing `config`, and
the values needed for C (section 3). Then:

1. Create the folder, the virtualenv and the project:

   ```bash
   mkdir -p <path> && cd <path>
   python3 -m venv .venv
   .venv/bin/pip install Django
   .venv/bin/django-admin startproject <settings-package> .
   ```

2. Write `requirements.txt` with the direct dependencies pinned to the
   installed versions (`Django==<version>`, from `.venv/bin/pip show
   Django`). Packages added later go in the same file.
3. Write a `.gitignore` with at least `.venv/`, `__pycache__/`,
   `*.pyc`, `db.sqlite3`, `.env`, `staticfiles/`.
4. Do not run `migrate`: the user applies the migrations.
5. Do not run `git init`: the user creates the repository.

From here on, every command runs in the project folder with
`.venv/bin/python`. A new project is now an existing project where every
component is missing: continue with section 3.

---

## 3. Analysis

Check each component and give it a state:

- **compliant**: it meets the rules → do not touch it;
- **different**: it exists but differs from the rules → list the
  differences;
- **missing**: it does not exist → it will be added.

| # | Component | Compliant when |
|---|---|---|
| A | `CLAUDE.md` | It exists and contains every section of `DJANGO_CODING_RULES.md`, with the same rules |
| B | `core` app | The `core` app exists, is in `INSTALLED_APPS`, and has the packages `<prefix>_models` and `<prefix>_utils`, each with an `__init__.py` |
| C | Constants and version | `.version` in the project root contains the version; `core/version.py` defines `get_version()` as `core/version.py` of this skill; `core/constants.py` defines `APP_NAME` and `VERSION = get_version()`; the settings define `VERSION = get_version()`; no other file of the project hardcodes the version, except the files that cannot read `.version` (see section 4, C) |
| D | Logger | It meets section 1 of `logger/SETUP_LOGGER.md` (check as in its section 2.1) |
| E | Base models | `BaseModel`, `BaseModelWithActivityLog` and `SoftDeletes` exist in `core/<prefix>_models/`, one per module, and behave as `helpers/base_model.py`, `helpers/base_model_with_activity_log.py` and `helpers/soft_deletes.py`; `core/apps.py` registers the subclasses with auditlog as `core/apps.py` of this skill; `django-auditlog` is installed, in `INSTALLED_APPS`, with its middleware |
| F | `BulkInsert` | `core/<prefix>_utils/bulk_insert.py` exists and behaves as `helpers/bulk_insert.py` |

If the project has a `core` app with another purpose, or keeps its
shared classes in another app (e.g. `common`, `utils`), do not create a
second one: ask the user which app to use, and use that app instead of
`core` in every path and import of this skill.

**Prefix** of the packages (`DJANGO_CODING_RULES.md`, section 5.6): if
the apps already have packages named `<something>_models`,
`<something>_views`, ..., propose that prefix; otherwise ask the user,
proposing the name of the project in lowercase (e.g. `infojuice`). New
project: ask it together with the values for C.

Values needed for C:

- `APP_NAME`: from `core/constants.py` if present, otherwise ask the user
  (propose the name of the folder or of the settings package);
- version: from `.version` if present; otherwise ask the user, proposing
  the version already written in the project (`VERSION` in
  `core/constants.py` or in the settings, `version` in
  `pyproject.toml`), or `0.1.0`.

To find where the version is hardcoded, search the project (excluding
the virtualenv, `node_modules/` and the migrations) for the current
version and for `VERSION` / `version` assignments: settings of
third-party libraries (e.g. `SPECTACULAR_SETTINGS["VERSION"]`, the
release of Sentry or APM), templates, management commands,
`pyproject.toml`, `package.json`, `Dockerfile` labels.

**Existing project**: show the user the table with the state of each
component and, for each **different** component, its differences. Ask
which components to apply and how to handle the different ones. Do not
change anything before the user answers.

**New project**: every component is missing; apply all of them.

---

## 4. Apply

Apply only the **missing** components, and the **different** ones the
user asked to change. Never rewrite a compliant component.

**Dependencies** (`DJANGO_CODING_RULES.md`, section 3.2):

- **existing project**: the agent never installs, updates or removes
  packages. When a component needs one, show the user the command to
  run with the tool of the project (e.g. `pip install django-auditlog`
  and the line for `requirements.txt`), wait for the user to run it,
  check that the package is installed, then continue;
- **new project**: the project does not exist yet, so the agent runs
  the commands itself, both to create it (section 2) and to install the
  packages of the components.

### A. `CLAUDE.md`

- Missing: copy `DJANGO_CODING_RULES.md` to `CLAUDE.md`, replacing
  `<prefix>` with the prefix everywhere. Change nothing else.
- Different: do not overwrite it. Add the missing sections of
  `DJANGO_CODING_RULES.md`; for rules in conflict with the existing
  ones, do what the user decided. Keep the content of the project
  (overview, domain notes, ...).
- Both cases: if `CLAUDE.md` has no section "Execution environment",
  add it at the end with the environment found in section 1, point 3
  (new project: the virtualenv `.venv`), as in section 3.1 of the
  rules.

### B. `core` app

1. `python manage.py startapp core`. Delete the `views.py` and
   `tests.py` it writes (they hold only a comment): views and tests go
   in packages. Empty `models.py` and `admin.py`: they are aggregators
   with imports only (`DJANGO_CODING_RULES.md`, section 5.6, rule 6),
   and the base models are abstract.
2. Create `core/<prefix>_models/` and `core/<prefix>_utils/`, each with
   an empty `__init__.py`. With an existing `core` app, create only the
   missing ones.
3. Add `"core"` to `INSTALLED_APPS`, after the Django and third-party
   apps and before the project apps.

`core` contains no concrete models: it gets no migrations.

### C. Constants and version

1. `.version` missing: create it in the project root with the version
   only (e.g. `0.1.0`) and a final newline. It is committed with the
   project: if `.gitignore` or `.dockerignore` exclude it, tell the user
   (the Docker image needs it).
2. `core/version.py` missing: copy `core/version.py` of this skill. It
   finds `.version` in the parent folder of `core/`: if the app is not in
   the project root, adapt `VERSION_FILE`.
3. `core/constants.py` missing: copy `core/constants.py` of this skill,
   replacing `__APP_NAME__`. File present: add only what is missing; a
   hardcoded `VERSION` becomes `VERSION = get_version()`.
4. In the settings module (with split settings, the base module) add,
   or replace a hardcoded `VERSION` with:

   ```python
   from core.version import get_version

   VERSION = get_version()
   ```

5. Every other place found in section 3 that hardcodes the version:
   - Python code and settings: use `VERSION` of the settings (inside the
     settings module) or `get_version()` (elsewhere);
   - templates: pass `settings.VERSION` in the context;
   - files that cannot read `.version` (`pyproject.toml`,
     `package.json`, ...): do not change them; list them in the report,
     so the user keeps them aligned or decides how to handle them.

   Apply this point only with the user's approval (section 3).

### D. Logger

Follow `logger/SETUP_LOGGER.md`, section 2.2 (Logger found) or 2.3
(Logger not found), then 2.4 (verify). C must be done first: the Logger
uses `APP_NAME`.

### E. Base models

1. If `django-auditlog` is not installed, install it and record it in the
   dependency file (see Dependencies above). Add `"auditlog"` to
   `INSTALLED_APPS` (before `"core"`), and
   `"auditlog.middleware.AuditlogMiddleware"` to `MIDDLEWARE` after
   `AuthenticationMiddleware` (it records the user who made the change).
   Do not apply its migrations.
2. Copy `helpers/base_model.py`,
   `helpers/base_model_with_activity_log.py` and `helpers/soft_deletes.py`
   to `core/<prefix>_models/`. Do not import them in `core/models.py`:
   they are abstract.
3. Copy `core/apps.py` of this skill to `core/apps.py`. If the existing
   `CoreConfig` has other code, add only the `ready()` method (or merge
   it into the existing one).
4. Do not change the existing models to extend the base models: the
   rule applies to new models. List the models that extend
   `models.Model` directly in the report.

### F. `BulkInsert`

Copy `helpers/bulk_insert.py` to `core/<prefix>_utils/bulk_insert.py`. It
uses the `Logger`, so it needs D done.

### Not applied

Do not reorder the fields of existing models or the columns of existing
tables: the field order rule applies to new tables and new fields. Do
not move the existing classes into packages: the package layout applies
to new classes (`DJANGO_CODING_RULES.md`, section 5.6, rule 7). Do
not change `DEFAULT_AUTO_FIELD` of an existing project: it would create
migrations for every model.

---

## 5. Verify

1. `python -m django --version` shows Django 4.2, 5.x or 6.x.
2. `python manage.py check` reports no new issues.
3. `python manage.py shell -c "from django.conf import settings; from
   core.constants import APP_NAME, VERSION; print(APP_NAME, VERSION,
   settings.VERSION)"` prints the application name and twice the content
   of `.version`.
4. `python -m py_compile <file>` on every Python file created or
   changed.
5. `python manage.py shell -c "from core.<prefix>_utils.logger import
   Logger; Logger.info('Setup test')"`: the message appears on stdout and in
   `logs/<project>-<YYYY-MM-DD>.log`.
6. `python manage.py shell -c "from
   core.<prefix>_models.base_model_with_activity_log import
   BaseModelWithActivityLog; from core.<prefix>_models.soft_deletes
   import SoftDeletes; from core.<prefix>_utils.bulk_insert import
   BulkInsert; print('ok')"` prints `ok`.
7. Every folder created by the setup in `core` has an `__init__.py`.
8. `python manage.py makemigrations core --check --dry-run` reports no
   changes for `core`.
9. Tests: new project, `python manage.py test` runs without errors;
   existing project, no test fails that passed in the baseline
   (section 1, point 6).

If a check fails because of the setup, fix it and run the checks again.
Report any check that still fails, with its output.

---

## 6. Report

Tell the user:

- the path of the project, the mode (new / existing), the Django
  version, how the project is run (virtualenv, Docker, ...) and the
  prefix of the packages;
- the table of section 3 with the final state of each component, and
  what was done for each one (added, changed, left unchanged);
- the files created or changed by the setup (beyond the Django skeleton
  for a new project), and the packages installed;
- existing project: the models that extend `models.Model` directly, the
  modules that hold more than one class of the same kind (e.g.
  `models.py`, `views.py`, `serializers.py`, with their number of
  classes), left where they are, and any test that fails both before
  and after the setup;
- the places that now read the version from `.version`, and the files
  that still hardcode it (section 4, C, point 5);
- the steps left to the user:
  - apply the migrations (`python manage.py migrate`), including the
    django-auditlog ones if it was installed;
  - new project: create the git repository and the first branch (the
    rules in `CLAUDE.md` forbid agents to write on `main` and to
    commit);
  - review the changes and commit them;
  - review `CLAUDE.md` and add the project overview.

---

## 7. Legacy project (Django older than 4.2)

The only change is `CLAUDE.md`. Do not touch anything else, even if it
does not meet the rules or is incompatible with them: no packages, no
`core` app, no `.version`, no Logger, no helper classes, no changes to
settings, code, dependencies or migrations. Do not run the tests: the
setup does not change the code.

### 7.1 Rules for a legacy project

The legacy `CLAUDE.md` contains only these sections of
`DJANGO_CODING_RULES.md`, copied unchanged, with their original numbers
and in their order:

| Section | Content |
|---|---|
| Glossary | Entity and managed model |
| 1 | Working method |
| 2.1 | Commits: agents never commit |
| 2.2 | Branch `main` |
| 2.3 | Migrations: agents never apply them; only the operations of the change |
| 2.4 | Data: unreliable, read and write queries allowed, no migrations |
| 3.1 | Execution environment: machine or Docker, ask and record it |
| 3.2 | Dependencies: the user installs them, the agent suggests |
| 3.3 | Configuration: environment, then `.env`, read from the configuration |
| 4 | Code style |
| 5.6 | Package layout (new classes only, existing code stays) |
| 6.1 | Field order |
| 7 | Testing (the test database exception of section 2.3) |

Sections 2 and 5 keep their titles; replace `<prefix>` with the prefix
of the project (section 3, without the other values). The file starts
with:

```markdown
# Django Coding Rules

Coding rules for this legacy project (Django <version>). They apply to
new code and to the lines being changed: the existing code stays as it
is, and the field types that this Django version does not have are
skipped. The section numbers are those of the full rules.
```

### 7.2 Apply

- `CLAUDE.md` missing: create it as in 7.1.
- `CLAUDE.md` present: compare it with 7.1 and show the user the missing
  sections and the rules in conflict with the existing ones. Ask how to
  proceed and do not change anything before the user answers. Then add
  the missing sections and, for the conflicts, do what the user decided.
  Keep the content of the project (overview, domain notes, ...).
- Both cases: add the section "Execution environment" at the end, with
  the environment found in section 1, point 3, unless it is already
  there.

### 7.3 Verify

1. `CLAUDE.md` contains the sections of 7.1, with the same rules.
2. `git status` (if the folder is a git repository) shows no change
   other than `CLAUDE.md`.

### 7.4 Report

Tell the user:

- the path of the project, the mode (legacy), the Django and Python
  versions, and how the project is run;
- what was done to `CLAUDE.md` (created, sections added, conflicts and
  how they were solved);
- that, being a legacy project, the helper classes, the Logger,
  `.version` and django-auditlog were not installed;
- the steps left to the user: review `CLAUDE.md`, add the project
  overview, and commit it.
