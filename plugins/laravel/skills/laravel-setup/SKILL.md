---
name: laravel-setup
description: Sets up a Laravel project with the coding rules (CLAUDE.md), the constants file, the project Logger and the helper classes. Creates a new Laravel 12 project, or completes an existing Laravel 11/12 project by adding only the missing parts. On legacy projects (Laravel older than 11) it writes only the coding rules in CLAUDE.md and leaves the project as it is. Use it when the user asks to prepare, create, set up or align a Laravel project.
argument-hint: "[project-path]"
---

# Laravel project setup

Set up the Laravel project in `$ARGUMENTS` with the rules and the classes
in this skill folder:

- **new project**: the folder does not exist or is empty. Create a
  Laravel 12 project, then set it up;
- **existing project**: the folder contains a Laravel 11 or 12 project.
  Add only the missing parts and do not touch the parts that already
  meet the rules;
- **legacy project**: the folder contains a project with Laravel older
  than 11. Write only the coding rules in `CLAUDE.md` (section 7): the
  rest of the project stays as it is.

Files of this skill (paths relative to this `SKILL.md`):

| File | Use |
|---|---|
| `LARAVEL_CODING_RULES.md` | Becomes the `CLAUDE.md` of the project |
| `bootstrap/constants.php` | `bootstrap/constants.php` (`APP_NAME`, `VERSION`) |
| `logger/` | Logger class, facade, alias and `SETUP_LOGGER.md` |
| `helpers/BaseModel.php` | `app/Models/BaseModel.php` |
| `helpers/BaseModelWithActivityLog.php` | `app/Models/BaseModelWithActivityLog.php` |
| `helpers/BulkInsert.php` | `app/Classes/BulkInsert.php` |

Read `LARAVEL_CODING_RULES.md` before starting: its rules apply to this
setup too. In particular: never run migrations, never commit, never
write on the `main` branch, change only what is needed.

The 80-column limit does not apply to Markdown files: the text this
skill writes in `CLAUDE.md` (for example the section "Execution
environment") has no line length limit, with one line per paragraph
or list item. Sections copied from the rules keep their text
unchanged.

---

## 1. Mode and checks

1. **Target folder**: `$ARGUMENTS`. If it is empty, ask the user for the
   path of the project.
   - The folder does not exist or is empty → **new project**.
   - The folder contains `artisan` and `composer.json` requires
     `laravel/framework` → **existing** or **legacy project**, by
     version (point 2).
   - Anything else → stop and ask the user.
2. **Laravel version** (existing folder only): read the installed
   version from `composer.lock` (package `laravel/framework`); it needs
   neither PHP nor `vendor/`. Without `composer.lock`, read the
   constraint in `composer.json` and ask the user to confirm the
   version.
   - 11.x, 12.x → **existing project**. If `vendor/` is missing, ask the
     user to run `composer install` first. Laravel 11 no longer receives
     security fixes: recent Composer versions block its releases because
     of security advisories, so never suggest `composer update`, and if
     a `composer require` fails for this reason, stop (do not suggest
     disabling the advisories policy). Mention it in the report.
   - Older than 11 → **legacy project**: do point 5, then go to
     section 7.
   - Newer than 12 → stop and tell the user.

New and existing project only:

3. **Environment and tools**: find how the project runs
   (LARAVEL_CODING_RULES.md, section 3.1): the section "Execution
   environment" of an existing `CLAUDE.md`, a Docker container
   (`Dockerfile` and `docker-compose.yml` / `compose.yaml`, or Laravel
   Sail), or the machine (always for a new project). If you cannot tell,
   ask the user how they run the project. Every command from here on
   runs in that environment, and it is written in `CLAUDE.md`
   (component A). Then check `php -v` (PHP >= 8.2) and `composer -V`;
   for a new project also `npm -v`. If one is missing, stop and tell
   the user.
4. **SQLite driver**: `php -m | grep -i pdo_sqlite`. Required for a new
   project (Laravel uses SQLite by default for database, sessions and
   tests) and for an existing project that uses SQLite
   (`DB_CONNECTION=sqlite` in `.env`, or SQLite in `phpunit.xml`). If the
   extension is missing, stop and tell the user (e.g. `php8.x-sqlite3`
   package on Debian/Ubuntu).

Existing and legacy project (point 6 only for an existing project):

5. **Git**: if the folder is a git repository, check the branch
   (`git branch --show-current`). On `main`, stop and ask the user to
   switch branch. If there are uncommitted changes (`git status`), tell
   the user and ask whether to proceed, so that the setup changes can be
   reviewed apart.
6. **Tests baseline**: run `php artisan test` and keep the result. It is
   compared with the result after the setup (section 5): failures that
   were already there are not caused by the setup. If the test database
   cannot be used (e.g. it does not exist yet, or the database user
   cannot reach it), tell the user and go on without the baseline.

---

## 2. Create the project (new project only)

1. Create the project **without the Composer scripts**: the scripts of
   `laravel/laravel` run `php artisan migrate`, which agents must never
   run.

   ```bash
   composer create-project laravel/laravel:^12.0 <path> --no-scripts
   ```

2. In the project folder, run only the safe steps of those scripts:

   ```bash
   cp .env.example .env
   php artisan key:generate
   touch database/database.sqlite
   ```

3. `npm install` (needed by `composer dev`).
4. Do not run `git init`: the user creates the repository.

From here on, every command runs in the project folder. A new project is
now an existing project where every component is missing: continue with
section 3.

---

## 3. Analysis

Check each component and give it a state:

- **compliant**: it meets the rules → do not touch it;
- **different**: it exists but differs from the rules → list the
  differences;
- **missing**: it does not exist → it will be added.

| # | Component | Compliant when |
|---|---|---|
| A | `CLAUDE.md` | It exists and contains every section of `LARAVEL_CODING_RULES.md`, with the same rules |
| B | Constants | `bootstrap/constants.php` defines `APP_NAME` and `VERSION`, and `bootstrap/app.php` loads it with `require_once` before `return Application::configure(...)` |
| C | Logger | It meets section 1 of `logger/SETUP_LOGGER.md` (check as in its section 2.1) |
| D | Base models | `App\Models\BaseModel` and `App\Models\BaseModelWithActivityLog` exist and behave as the files in `helpers/`, and `spatie/laravel-activitylog` is installed |
| E | `BulkInsert` | `App\Classes\BulkInsert` exists and behaves as `helpers/BulkInsert.php` |
| F | Test database | `phpunit.xml` (or `.env.testing`) makes the tests use the same `DB_CONNECTION` as the project and a database other than the development one (`:memory:` with SQLite) |

Values needed for B:

- `APP_NAME`: from `bootstrap/constants.php` if present, otherwise ask
  the user (propose `APP_NAME` from `.env`, or the folder name);
- `VERSION`: from `bootstrap/constants.php` if present, otherwise ask
  the user (propose `version` from `composer.json` if present, or
  `0.1.0`).

Value needed for F, when the project does not use SQLite: the name of
the test database (ask the user, proposing `<development database>_test`).

**Existing project**: show the user the table with the state of each
component and, for each **different** component, its differences. Ask
which components to apply and how to handle the different ones. Do not
change anything before the user answers.

**New project**: every component is missing; ask only the values for B,
then apply all of them.

---

## 4. Apply

Apply only the **missing** components, and the **different** ones the
user asked to change. Never rewrite a compliant component.

**Dependencies** (`LARAVEL_CODING_RULES.md`, section 3.2):

- **existing project**: the agent never installs, updates or removes
  packages. When a component needs one, show the user the command to
  run (e.g. `composer require spatie/laravel-activitylog`), wait for the
  user to run it, check that the package is installed, then continue;
- **new project**: the project does not exist yet, so the agent runs
  the commands itself, both to create it (section 2) and to install the
  packages of the components.

### A. `CLAUDE.md`

- Missing: copy `LARAVEL_CODING_RULES.md` to `CLAUDE.md`, unchanged.
- Different: do not overwrite it. Add the missing sections of
  `LARAVEL_CODING_RULES.md`; for rules in conflict with the existing
  ones, do what the user decided. Keep the content of the project
  (overview, domain notes, ...).
- Both cases: if `CLAUDE.md` has no section "Execution environment",
  add it at the end with the environment found in section 1, point 3,
  as in section 3.1 of the rules.

### B. Constants

- `bootstrap/constants.php` missing: copy `bootstrap/constants.php` of
  this skill, replacing `__APP_NAME__` and `__VERSION__`.
- File present without a constant: add only the missing constant.
- Not loaded: in `bootstrap/app.php`, after the `use` statements and
  before `return Application::configure(...)`, add:

  ```php
  require_once __DIR__.'/constants.php';
  ```

### C. Logger

Follow `logger/SETUP_LOGGER.md`, section 2.2 (Logger found) or 2.3
(Logger not found), then 2.4 (verify). B must be done first: the Logger
uses `APP_NAME`.

### D. Base models

1. If `spatie/laravel-activitylog` is not installed:
   - install it (`composer require spatie/laravel-activitylog`; see
     Dependencies above);
   - publish its migrations and config, unless they are already present
     in `database/migrations/` and `config/activitylog.php`:

     ```bash
     php artisan vendor:publish \
         --provider="Spatie\Activitylog\ActivitylogServiceProvider" \
         --tag="activitylog-migrations"
     php artisan vendor:publish \
         --provider="Spatie\Activitylog\ActivitylogServiceProvider" \
         --tag="activitylog-config"
     ```

     Do not run the migrations.
2. Copy the missing files among `helpers/BaseModel.php` and
   `helpers/BaseModelWithActivityLog.php` to `app/Models/`.
3. Do not change the existing models to extend the base models: the
   rule applies to new models. List the models that extend `Model`
   directly in the report.

### E. `BulkInsert`

Copy `helpers/BulkInsert.php` to `app/Classes/BulkInsert.php`. It uses
the `Logger` alias, so it needs C done.

### F. Test database

In `phpunit.xml`, set the database of the tests on the same engine as
the project (`DB_CONNECTION` of `.env`):

- SQLite (always for a new project): `DB_CONNECTION=sqlite` and
  `DB_DATABASE=:memory:` (uncomment the lines in Laravel 11);
- other engines: `DB_CONNECTION` of the project and `DB_DATABASE` with
  the name of the test database. Remove the SQLite lines, if present.
  The agent does not create the database (section 2.3 of the rules:
  no DDL by hand): the user creates it (section 6).

### Not applied

Do not install `thiagoprz/eloquent-composite-key`: it is added when a
table without a single primary key is needed. Do not reorder the columns
of existing tables: the column order rule applies to new tables and new
columns.

---

## 5. Verify

1. `php artisan --version` shows Laravel 11 or 12.
2. `php artisan tinker --execute="echo APP_NAME, ' ', VERSION;"` prints
   the application name and version.
3. `php -l` on every file created or changed in `app/` and `bootstrap/`.
4. `php artisan tinker --execute="Logger::info('Setup test');"`: the
   message appears on stdout and in `storage/logs/`.
5. `php artisan tinker --execute="echo class_exists(App\Models\BaseModelWithActivityLog::class) && class_exists(App\Classes\BulkInsert::class) ? 'ok' : 'ko';"`
   prints `ok`.
6. `php artisan test`: new project, the example tests pass; existing
   project, no test fails that passed in the baseline (section 1,
   point 6).

If a check fails because of the setup, fix it and run the checks again.
Report any check that still fails, with its output.

---

## 6. Report

Tell the user:

- the path of the project, the mode (new / existing) and the Laravel
  version;
- the table of section 3 with the final state of each component, and
  what was done for each one (added, changed, left unchanged);
- the files created or changed by the setup (beyond the Laravel skeleton
  for a new project);
- existing project: the models that extend `Model` directly, and any
  test that fails both before and after the setup;
- the steps left to the user:
  - run the migrations (`php artisan migrate`), including the Spatie
    activity log ones if they were published;
  - project not on SQLite: create the test database set in
    `phpunit.xml`, if it does not exist yet;
  - new project: create the git repository and the first branch (the
    rules in `CLAUDE.md` forbid agents to write on `main` and to
    commit);
  - review the changes and commit them;
  - review `CLAUDE.md` and add the project overview.

---

## 7. Legacy project (Laravel older than 11)

The only change is `CLAUDE.md`. Do not touch anything else, even if it
does not meet the rules or is incompatible with them: no packages, no
constants file, no Logger, no helper classes, no changes to
configuration, code, dependencies or migrations. Do not run the tests:
the setup does not change the code.

### 7.1 Rules for a legacy project

The legacy `CLAUDE.md` contains only these sections of
`LARAVEL_CODING_RULES.md`, copied unchanged, with their original numbers
and in their order:

| Section | Content |
|---|---|
| Glossary | Entity and managed model |
| 1 | Working method |
| 2.1 | Commits: agents never commit |
| 2.2 | Branch `main` |
| 2.3 | Migrations: agents never run them; only the operations of the change |
| 2.4 | Data: unreliable, read and write queries allowed, no migrations |
| 3.1 | Execution environment: machine or Docker, ask and record it |
| 3.2 | Dependencies: the user installs them, the agent suggests |
| 3.3 | Configuration: environment, then `.env`, read from the configuration |
| 4 | Code style |
| 5.6 | Code structure (new classes only, existing code stays) |
| 6.1 | Column order |
| 7 | Testing |

Sections 2 and 5 keep their titles. The file starts with:

```markdown
# Laravel Coding Rules

Coding rules for this legacy project (Laravel <version>). They apply to
new code and to the lines being changed: the existing code stays as it
is, and the features that this Laravel version does not have are
skipped. The section numbers are those of the full rules.
```

### 7.2 Apply

- `CLAUDE.md` missing: create it as in 7.1.
- `CLAUDE.md` present: compare it with 7.1 and show the user the missing
  sections and the rules in conflict with the existing ones. Ask how to
  proceed and do not change anything before the user answers. Then add
  the missing sections and, for the conflicts, do what the user decided.
  Keep the content of the project (overview, domain notes, ...).
- Both cases: if the execution environment is clear from the project
  (section 3.1 of the rules), add the section "Execution environment"
  at the end, unless it is already there. If it is not clear, do not
  ask: the agent asks the first time it needs to run a command.

### 7.3 Verify

1. `CLAUDE.md` contains the sections of 7.1, with the same rules.
2. `git status` (if the folder is a git repository) shows no change
   other than `CLAUDE.md`.

### 7.4 Report

Tell the user:

- the path of the project, the mode (legacy) and the Laravel version;
- what was done to `CLAUDE.md` (created, sections added, conflicts and
  how they were solved);
- that, being a legacy project, the constants file, the Logger, the
  helper classes and the Spatie activity log were not installed;
- the steps left to the user: review `CLAUDE.md`, add the project
  overview, and commit it.
