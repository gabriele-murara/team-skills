---
name: django-apm
description: Adds Elastic APM to an existing Django project - elastic-apm 6.x agent configured from environment variables and disabled by default, tracing middleware, optional tracing of processes without HTTP (daemons, importers, workers run as management commands), the check_apm management command, tests and the APM_CONFIGURATION.md guide. Use it when the user asks to install, add, configure or align Elastic APM (application performance monitoring) in a Django project.
argument-hint: "[project-path]"
---

# Elastic APM in a Django project

Add Elastic APM to the Django project in `$ARGUMENTS` (the current folder if empty). Run the sections in order. Do not skip the analysis (section 1): the next sections depend on its results.

Files of this skill (paths relative to this `SKILL.md`):

| File | Use |
|---|---|
| `settings/elastic_apm.py` | Snippet for the base settings module (section 3): not a module to copy |
| `utils/apm_traced_program.py` | `ApmTracedProgram`, traces a process without HTTP (section 5) |
| `commands/check_apm.py` | `check_apm` command with `django-rich` (section 6) |
| `commands/check_apm_plain.py` | `check_apm` command without `rich` (section 6), copied as `check_apm.py` |
| `tests/test_apm_traced_program.py` | Tests of `ApmTracedProgram` (section 7); `__TRACED_PROGRAM_MODULE__` is the dotted path of the module |
| `tests/test_check_apm.py` | Tests of `check_apm`, valid for both variants (section 7) |
| `doc/APM_CONFIGURATION.md` | Template of the guide for the project (section 8.2) |

The Python files are tested with Django 5.2, `elastic-apm` 6.26 and `django-rich` 2.2. They follow 80 columns and `str.format()`; if the project has different style rules, adapt them.

---

## 0. Rules

1. **Project rules.** If the project has a `CLAUDE.md` (or an equivalent file of rules for agents), read it before starting: its rules prevail over this skill (code style, package layout, language, execution environment). Without rules, follow the conventions of the existing code.
2. **Branch.** Do not work on `main` or `master`. If you are on one of them, stop and ask the user to change branch.
3. **Dependencies.** Do not install, upgrade or remove packages. Propose to the user the lines for the dependency file and the command to run (with Docker: the rebuild of the image), then wait for the confirmation. Write the lines in the dependency file yourself only if the user asks.
4. **Migrations.** APM needs no migrations: do not run `migrate` and do not create migrations.
5. **Commits.** Do not commit: at the end list the changed files.
6. **Secrets.** Never print or copy tokens and passwords (`APM_SECRET_TOKEN`, database credentials). Do not open local `.env` files that contain secrets, except the example ones (`.env.sample`, `.env.example`) and the versioned development ones.
7. **Minimal changes.** Change only what APM needs. Report other problems to the user without fixing them.
8. **Language.** Code, comments and messages of the code in English; documentation and dialogue with the user in the language of the project.

---

## 1. Analysis

Collect this information and summarize it to the user before changing the code.

| # | What | How to find it |
|---|---|---|
| 1 | Execution environment | `Dockerfile` and `docker-compose.yml` → Docker (`docker compose exec <service> ...`); otherwise a virtualenv. The section "Execution environment" of `CLAUDE.md`, if present. When in doubt, ask |
| 2 | Python version | `python --version` **in the execution environment** (the local Docker image can be older than the `Dockerfile`: compare them) |
| 3 | Django version | `python -m django --version` |
| 4 | Settings module | `DJANGO_SETTINGS_MODULE` in `manage.py`, `wsgi.py`, `uwsgi.ini`, start scripts. With split settings, find the base module and the modules that extend it |
| 5 | Environment variables | `django-environ` (`env = Env()`), `os.environ`, `python-decouple`, ... Use the same mechanism |
| 6 | Existing APM configuration | Search `ELASTIC_APM`, `APM_ACTIVE`, `elasticapm` in settings, code and dependency files. Note the agent version, hard-coded values and tokens written in the code |
| 7 | Application server | `uwsgi.ini*`, `gunicorn.conf.py`, start command in the `Dockerfile` or in the scripts (`run.sh`, `docker-entrypoint.sh`) |
| 8 | Processes without HTTP | Management commands that run as daemons or loops (importers, workers, schedulers), Celery, cron. For each one: where the function run at every cycle is called |
| 9 | URLs not to trace | Health check, version, streams or downloads of binary files (`urls.py`) |
| 10 | Tests | Layout (`tests/`, `<prefix>_tests/`), command (`manage.py test --settings ...` or `pytest`), test settings |
| 11 | Example configuration files | `.env.sample`, `.env.dev`, settings templates (`*.j2`), `docker-compose*.yml` |
| 12 | Documentation | Documentation folder (`doc/`, `docs/`, `wiki/`) |

Then run the **test baseline**: run the whole suite and save the result (number of tests, errors and failures, with their names). At the end you compare it with the result after the changes: errors already present do not depend on your work.

### Questions for the user

Ask only what the analysis does not answer:

1. Which processes without HTTP (point 8) must be traced?
2. URL of the APM Server and whether it needs a secret token (only for the final check; do not write them in the code).
3. If the Django or Python version rules out `elastic-apm` 6.x or `django-rich` (section 2), how to proceed.

---

## 2. Dependencies

Reference versions:

```
elastic-apm>=6.20.0,<7.0.0
django-rich==<compatible version>
```

1. **elastic-apm 6.x.** Required: `SPAN_STACK_TRACE_MIN_DURATION` and `elasticapm.set_transaction_outcome` do not exist in 5.x. Before proposing it, check on the official agent documentation or on PyPI that the version supports the Django and Python versions of the project. If the project already has `elastic-apm` 5.x, replace the line.
2. **django-rich.** Used by `check_apm`. Find the compatible version on PyPI (`https://pypi.org/pypi/django-rich/json` for the releases, `https://pypi.org/pypi/django-rich/<version>/json` for the fields `requires_dist`, `requires_python` and the classifiers `Framework :: Django`). For example 1.0.0 supports Django 2.2–4.0 and Python >= 3.6; recent releases support only recent Django versions. It also installs `rich`. If no version is compatible, use the variant without `rich` (section 6).
3. **requests.** Used by `check_apm`. If it is not installed, add it.
4. Check conflicts with pinned packages (for example `urllib3`: elastic-apm 6.x needs `urllib3<3,!=2.0.0`).
5. Propose the lines and the command to the user (rule 0.3). With Docker the image must be rebuilt (for example `docker compose build`) and the containers recreated.

---

## 3. Settings

In the base settings module (the one that defines `INSTALLED_APPS` and `MIDDLEWARE`), from `settings/elastic_apm.py`:

1. `import socket` with the other imports of the module.
2. **Activation flag**: `APM_ACTIVE`, near the other general settings.
3. **`ELASTIC_APM` block**, after `INSTALLED_APPS` and `MIDDLEWARE`, with the `SECRET_TOKEN` and the `if APM_ACTIVE:` block. Replace `__SERVICE_NAME__` with the name of the project in lowercase with underscores (for example `my_project`) and adapt `TRANSACTIONS_IGNORE_URLS` to the URLs found in section 1 (point 9). If the project does not use `django-environ`, translate the `env.*` calls into the mechanism of the project, keeping variable names and defaults.
4. **Flags of the processes without HTTP**: one for every process to trace (section 1, point 8), named `APM_<PROCESS>_ACTIVE` (for example `APM_IMPORTER_ACTIVE`, `APM_WORKER_ACTIVE`), used only together with `APM_ACTIVE`. Remove `APM_IMPORTER_ACTIVE` if no process is traced.

Notes:

- `INSTALLED_APPS` and `MIDDLEWARE` must be **lists** (not tuples) for `append` and `insert`. If they are tuples, convert them or adapt the code.
- `SECRET_TOKEN` is added only when not empty: with Docker Compose a variable interpolated but not defined (`${APM_SECRET_TOKEN}`) arrives as an empty string.
- If an `ELASTIC_APM` block already exists, update it: remove tokens written in the code (commented ones too), a fixed `SERVER_URL`, a fixed `ENABLED: True`.
- With split settings: if a module that extends the base redefines `APM_ACTIVE` or `ELASTIC_APM`, it must repeat the `if APM_ACTIVE:` block (as its comment says). Check the existing modules and the templates (`*.j2`).

---

## 4. Application server

### uWSGI

The `uwsgi.ini` file (and its examples or templates) needs both:

```ini
enable-threads = true                ; Required for APM: background threads
lazy-apps = true                     ; Load app in workers, not master (required for APM)
```

Without `enable-threads` the agent does not create its sending threads; without `lazy-apps` the agent is initialized in the master and the workers inherit an inconsistent state after the fork.

### Gunicorn and other servers

Do not load the application in the master process before the fork of the workers (in Gunicorn: `preload_app`/`--preload` disabled). If the project must use preload, tell the user and read the agent documentation before proceeding.

---

## 5. Processes without HTTP

The middleware traces only HTTP requests. For the processes that run in a loop (daemons, importers, workers based on management commands) every run of the function of the loop becomes an APM transaction. Skip this section if the user does not want to trace any process.

**Celery:** do not use `ApmTracedProgram`. The agent has a dedicated integration (`elasticapm.contrib.celery`, `register_instrumentation`): follow its documentation and tie it to the same kind of flag.

### 5.1 `ApmTracedProgram`

Copy `utils/apm_traced_program.py`. Location: according to the project rules (with the package layout of the `django-setup` rules, section 5.6: `<app>/<prefix>_utils/apm_traced_program.py`, with an empty `__init__.py` in the package; otherwise a utility module of the app that contains the process).

- `get_client()` returns the client created by the `elasticapm.contrib.django` app, which also instruments the database queries (visible as spans). It works in management commands, which load the Django apps.
- The exception is raised again: the behaviour of the process does not change.
- The program is called without arguments. If the function of the loop needs arguments, wrap it (for example with `functools.partial`) before passing it.
- Choose a meaningful `transaction_type` and `name` (for example `importer` / `scan_folder`, `worker` / `process_queue`).

### 5.2 Wiring the process

Where the process receives or calls the function of the loop, wrap it only if both flags are active; otherwise the code stays as it was. Example:

```python
def _init_daemon(self):
    main_program = ProcessFiles.scan_folder
    if settings.APM_ACTIVE and settings.APM_IMPORTER_ACTIVE:
        main_program = ApmTracedProgram(main_program, "scan_folder")
    self.daemon = daemonize.Daemonize(main_program)
```

If the loop is written in the command itself (`while True: ...`), move the body of one iteration into a function and call the `ApmTracedProgram` instance at every iteration. Do not change the logic of the loop.

---

## 6. `check_apm` command

In `<app>/management/commands/check_apm.py`, in the main app of the project (with `__init__.py` in `management/` and `commands/`). It shows the configuration with the token masked and checks that the APM Server is reachable and accepts the token.

- With a compatible `django-rich`: copy `commands/check_apm.py`. It uses the console of `RichCommand` (`self.console`), which writes on the `stdout` passed to the command, so it can be tested with `call_command(..., stdout=...)`.
- Without `django-rich`: copy `commands/check_apm_plain.py` as `check_apm.py`. It writes with `self.stdout.write` and `self.style`; the status strings (`Server reachability: OK`, `Authentication: FAILED`, `Authentication failed - check SECRET_TOKEN`, `APM is not active`, `SERVER_URL is not configured`, `Cannot connect`) are the same as the rich variant, for the tests and the documentation.

In both, set `PROCESS_FLAGS` to the flags of section 3, step 4 (empty list if no process is traced).

---

## 7. Tests

In the test layout of the project (with the package layout of the `django-setup` rules: `<app>/<prefix>_tests/`). The tests use `SimpleTestCase`: none needs the database. They never call the real APM Server: `requests` and the APM client are mocked with `unittest.mock`.

1. `tests/test_apm_traced_program.py` (only if a process is traced): copy it as `test_apm_<process>.py` and replace `__TRACED_PROGRAM_MODULE__` with the dotted path of the module of section 5.1 (for example `shop.shop_utils.apm_traced_program`).
2. In the same file, add a class that checks the wiring of section 5.2 with the three combinations of the flags: both active → instance of `ApmTracedProgram`; `APM_ACTIVE=True` and process flag off → original function; `APM_ACTIVE=False` and process flag on → original function. Use `override_settings` and mock the class that receives the function (for example the daemon) to read the argument it is created with.
3. `tests/test_check_apm.py`: copy it unchanged. Cases: APM not active, `SERVER_URL` missing, server reachable and token accepted (token masked and absent from the output, `Authorization` header), token refused (401), server not reachable.

---

## 8. Configuration and documentation

### 8.1 Example environment files

In the versioned files (`.env.sample`, `.env.dev`, ...), APM disabled and the optional variables commented out. Do not write an empty `ELASTIC_APM_SERVER_URL=`: leave it commented out, so the default stays `None`.

```bash
# Elastic APM (see doc/APM_CONFIGURATION.md)
APM_ACTIVE=false
#ELASTIC_APM_SERVER_URL=http://apm-server:8200
#APM_SERVICE_NAME=<service_name>
#APM_HOSTNAME=
#APM_SECRET_TOKEN=
#ELASTIC_APM_DEBUG=false
#APM_TRANSACTION_SAMPLE_RATE=0.1
#APM_SPAN_STACK_TRACE_MIN_DURATION=100ms
# Trace every run of the importer as an APM transaction
APM_IMPORTER_ACTIVE=false
```

One `APM_<PROCESS>_ACTIVE=false` line for every flag; none if no process is traced. Fix the path of the guide (section 8.2).

If the settings are generated from a template (for example `settings/docker.py.j2` with `j2`), check that the generated module imports the base (`from .defaults import *`) and that the variables reach the container (`env_file` or `environment` in `docker-compose.yml`). If the template redefines `APM_ACTIVE` or `ELASTIC_APM`, apply the note of section 3 on split settings.

### 8.2 `APM_CONFIGURATION.md` guide

Copy `doc/APM_CONFIGURATION.md` in the documentation folder of the project (create `doc/` if there is none) and translate it into the language of the project documentation. Replace the placeholders:

- `__PROJECT_NAME__`: name of the project;
- `__SERVICE_NAME__`: default of `APM_SERVICE_NAME` (section 3);
- `__PROCESS_FLAG_ROWS__`: one table row for every `APM_<PROCESS>_ACTIVE` flag (default `false`, not required, "Traces every run of `<function>` of `<command>`; used only with `APM_ACTIVE=true`"); remove the line if there are none;
- `__IGNORED_URLS__`: the URLs of `TRANSACTIONS_IGNORE_URLS`;
- `__PROCESS_SECTION__`: for every traced process, how it is traced (transaction type and name, flag to enable it, the advice to use a different `APM_SERVICE_NAME` for it); otherwise one sentence saying that the processes without HTTP are not traced;
- `__SERVER_SECTION__`: the settings of section 4 for the application server of the project (uWSGI or Gunicorn), with the reason;
- `__CHECK_APM_COMMAND__`: the command to run `check_apm` in the environment of the project (for example `docker compose exec web python manage.py check_apm`).

### 8.3 `CLAUDE.md`

If the project has a `CLAUDE.md`, add a short section (Markdown has no line length limit, one line per list item):

```markdown
## Elastic APM

- Optional, disabled by default (`APM_ACTIVE=false`). Configuration in the `ELASTIC_APM` block of `<settings module>`, read from the environment variables listed in `<doc path>/APM_CONFIGURATION.md`.
- The API is traced by the `elasticapm` middleware; <process> traces every run of `<function>` as a transaction only when `APM_<PROCESS>_ACTIVE=true` too (`<path>/apm_traced_program.py`).
- Check the configuration and the connection to the APM Server with `python manage.py check_apm`.
```

Remove the second item's part on processes if none is traced.

---

## 9. Verify

Run every command in the execution environment of the project. If a check fails because of the changes, fix and repeat.

1. `python -m py_compile` on every Python file created or changed.
2. Installed dependencies (after the user's confirmation): `pip list` shows `elastic-apm` 6.x and, if used, `django-rich`.
3. `python manage.py check` with no new issues, both with APM off and with `APM_ACTIVE=true` (and the process flags on) passed as environment variables to the command. With `APM_ACTIVE=true` also pass a dummy `ELASTIC_APM_SERVER_URL` (for example `http://127.0.0.1:8200`), otherwise the agent prints `Configuration error: value for SERVER_URL is required`.
4. Whole test suite: the new tests pass and no test that passed in the baseline fails. Report the errors already present as such.
5. `python manage.py check_apm` with APM off (message `APM is not active`) and, if the user configured the server, with APM on (`Server reachability: OK`, `Authentication: OK`).
6. Real test, if the user configured the APM Server in the environment:
   - **Django with `DEBUG=True`** (usual in development): the middleware does not send transactions if `ELASTIC_APM_DEBUG` is `false`. Ask the user to set `ELASTIC_APM_DEBUG=true` before the test (development only, never in production).
   - Set `APM_TRANSACTION_SAMPLE_RATE=1.0` for the test, otherwise only 10% of the requests are sampled.
   - **uWSGI does not reload changed code** (unless `py-autoreload`): restart the service or the container before testing.
   - Make some HTTP requests (public endpoints, protected endpoints without credentials for a 401/403, a missing URL for a 404, an ignored URL) and tell the user what to look for in Kibana: service `<service_name>`, transactions named after the views, spans of the queries, ignored URLs absent.
   - For the traced processes: with the flag on, check in Kibana the transactions of type `importer` (or the chosen type).

---

## 10. Report

Report to the user:

- the Python, Django and `elastic-apm` versions used, and how the project runs;
- for every section: what was added or changed, or why it was skipped;
- the new environment variables, with defaults and whether they are required;
- the result of the checks (baseline and final result of the tests, `check_apm`, real test);
- the actions for the deploy: rebuild the image, add `lazy-apps = true` (or the equivalent) to the production configuration of the application server, set `APM_ACTIVE`, `ELASTIC_APM_SERVER_URL`, `APM_SECRET_TOKEN` and the process flags, set a different `APM_SERVICE_NAME` for every service (API, importer, worker) to tell them apart in Kibana, check with `check_apm` after the deploy;
- the problems found and not fixed (rule 0.7);
- the list of the changed files, without committing.

---

## Common errors

| Symptom | Cause | Solution |
|---|---|---|
| No transactions in Kibana in development | Django `DEBUG=True` and `ELASTIC_APM_DEBUG=false` | `ELASTIC_APM_DEBUG=true`, development only |
| Few transactions in Kibana | `TRANSACTION_SAMPLE_RATE` is 0.1 by default | `APM_TRANSACTION_SAMPLE_RATE=1.0`, for tests only |
| Code changes not visible | uWSGI does not reload the code | Restart the service or the container |
| `AttributeError` on `set_transaction_outcome` or unknown options | Agent 5.x still installed | Upgrade to 6.x and rebuild the image |
| Python version different from the `Dockerfile` | Local image built before the change of the `Dockerfile` | Rebuild the image |
| Empty `SECRET_TOKEN` sent to the server | Variable interpolated but not defined in Docker Compose | Add the token only when not empty (section 3) |
| `Configuration error: value for SERVER_URL is required` | `APM_ACTIVE=true` without `ELASTIC_APM_SERVER_URL` | Set the URL (a dummy one for `check`) |
| Unstable uWSGI workers or missing data | `lazy-apps` or `enable-threads` missing | Section 4 |
| APM active in the settings but middleware missing | A derived settings module redefines `APM_ACTIVE` without repeating the `if APM_ACTIVE:` block | Section 3, split settings |
