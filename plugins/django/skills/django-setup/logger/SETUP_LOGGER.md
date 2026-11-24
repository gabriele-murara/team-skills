# Logger setup

Instructions for an agent that sets up a Django project. The project must
log through the `Logger` class described here, not through `logging` or
`print()` (see `../DJANGO_CODING_RULES.md`, section 5.2).

`<prefix>` is the prefix of the packages of the project (see
`../SKILL.md`, section 3). Reference file in this folder:

| File | Target in the project |
|---|---|
| `logger.py` | `core/<prefix>_utils/logger.py` (replace `__PREFIX__`) |

Before writing any file, follow the rules in
`../DJANGO_CODING_RULES.md`, section 2: check the branch (never write on
`main`) and never commit.

---

## 1. Required configuration

The Logger is correctly set up when **all** the points below hold.

1. **Class** `core.<prefix>_utils.logger.Logger`
   (`core/<prefix>_utils/logger.py`), with the same
   behaviour as `logger.py` in this folder:
   - class methods `debug`, `info`, `warning`, `error`, `alert`
     (`msg`, `name="main"`; `alert` logs at `CRITICAL`) and
     `sql(queryset)`, which logs the SQL of a QuerySet with the
     parameters replaced;
   - lazy initialization on first use with `init(APP_NAME, name)`, one
     Python logger per `name` (`<APP_NAME>.<name>`, not propagated to
     the root logger);
   - log format `[%(asctime)s] <APP_NAME>/%(process)d.%(levelname)s:
     %(message)s (%(pathname)s:%(lineno)d %(funcName)s)` with date
     `%Y-%m-%d %H:%M:%S`;
   - daily file `<LOG_FILE without extension>-YYYY-MM-DD.log`
     (`DailyFileHandler`, no limit, files never renamed), with level
     `LOG_LEVEL`;
   - stdout handler only in the management commands
     (`running_in_console()`), with level `CONSOLE_LOG_LEVEL`, and
     `colorlog.ColoredFormatter` when `colorlog` is installed;
   - `sys.excepthook` that logs the uncaught exceptions and calls the
     previous hook;
   - the log line shows the file and line of the caller
     (`stacklevel=2`), not of `logger.py`.
2. **Constant `APP_NAME`** in `core/constants.py`, used by the Logger as
   the logger name (see `../SKILL.md`, section 4, component C).
3. **Settings** in the settings module of the project, read from the
   environment with the mechanism of the project (section 3.3 of
   `../DJANGO_CODING_RULES.md`):

   ```python
   LOG_FILE = os.environ.get(
       "LOG_FILE", str(BASE_DIR / "logs" / "<project>.log")
   )
   LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")
   CONSOLE_LOG_LEVEL = os.environ.get("CONSOLE_LOG_LEVEL", "DEBUG")
   ```

4. **Log folder** ignored by git: `logs/.gitignore` contains `*` and
   `!.gitignore`, one per line (or the folder of `LOG_FILE` is ignored in
   another way).
5. **Environment**: `.env.example` (or `.env.sample`), when present,
   contains:

   ```
   LOG_FILE=
   LOG_LEVEL=DEBUG
   CONSOLE_LOG_LEVEL=DEBUG
   ```

6. **Package** (optional, for colored console output): `colorlog`.

Django's `LOGGING` setting is not changed: it keeps handling the logs of
Django and of the other libraries.

---

## 2. Procedure

### 2.1 Check

Look for an existing Logger in the project:

- `core/<prefix>_utils/logger.py`;
- any other class or module named `Logger` / `logger`
  (`grep -rn "class Logger" --include=*.py .`, excluding the
  virtualenv);
- the settings `LOG_FILE`, `LOG_LEVEL`, `CONSOLE_LOG_LEVEL`, and a
  custom `LOGGING` setting that writes the project logs.

Compare what you find with every point of section 1.

### 2.2 Logger found

- **It meets section 1**: use it. Do not change or replace it.
- **It differs from section 1** (missing points, different behaviour,
  different names): do not overwrite it. List the differences to the user
  and ask how to proceed. Add only the missing points that do not touch
  the existing code (e.g. `CONSOLE_LOG_LEVEL` in `.env.example`) after
  the user agrees.

### 2.3 Logger not found

Create it and set it up:

1. Copy `logger.py` to `core/<prefix>_utils/logger.py`, replacing
   `__PREFIX__` (`core/<prefix>_utils/` has an `__init__.py`: see
   `../SKILL.md`, section 4, component B).
2. Make sure `core/constants.py` defines `APP_NAME`: see `../SKILL.md`,
   section 4, component C.
3. Add the settings of section 1, point 3 to the settings module (with
   split settings, to the base module), with `<project>` replaced by the
   project name in lowercase (e.g. `logs/myproject.log`). If the project
   reads the environment with another mechanism, use it.
4. Create `logs/.gitignore` (section 1, point 4), unless the folder is
   already ignored.
5. Add the variables of section 1, point 5 to `.env.example` and, if
   present, to `.env`.
6. Ask the user whether they want `colorlog` (the Logger works without
   it). If so, install it as in `../SKILL.md`, section 4
   (Dependencies).

### 2.4 Verify

1. `python manage.py shell -c "from core.<prefix>_utils.logger import
   Logger; Logger.info('Logger test')"`: the message appears on stdout and in
   `logs/<project>-<YYYY-MM-DD>.log`.
2. The log line contains the file and line of the caller, not
   `logger.py`.
3. Outside the management commands (e.g. a web request served by
   gunicorn/uwsgi) the message is written only to the file.

At the end, list the files created or changed so the user can review and
commit them.
