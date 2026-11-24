# Django Coding Rules

Coding and implementation rules for Django projects.

Rules marked **(helper)** use a helper class of the project, listed in
section 8. Names in the examples (tables, classes, apps) are
placeholders: adapt them. `<prefix>` is the prefix of the packages of
the project (section 5.6).

---

## Glossary

- **Entity**: a domain object managed by the system, made of a model,
  its views and its serializers. Creating an entity means creating all
  its parts.
- **Managed model**: a model used by the system through forms, tables
  or lists, or that needs a new table in the database. Creating an
  entity always creates a managed model.

---

## 1. Working method

### 1.1 Think before coding

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them: do not pick one
  silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop, name what is confusing and ask.

### 1.2 Simplicity first

Write the minimum code that solves the problem, nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that was not requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Test: "Would a senior engineer say this is overcomplicated?" If yes,
simplify.

### 1.3 Surgical changes

Touch only what you must. Clean up only your own mess.

- Do not "improve" adjacent code, comments or formatting.
- Do not refactor things that are not broken.
- New lines, and existing lines that the task changes, follow the
  coding rules (section 4), even if the function or class then mixes
  two styles. The other lines keep their style.
- If most of the function or class you are changing already follows
  the coding rules, ask the user whether to bring the rest of it in line
  too, and do it only if the user agrees.
- Exception: when the user explicitly asks to format a function, a
  class or a file with the coding rules, format exactly that part
  (section 4.1).
- If you notice unrelated dead code, mention it: do not delete it.
- Remove imports, variables and functions that **your** changes made
  unused. Do not remove pre-existing dead code unless asked.

Every changed line must trace directly to the request.

### 1.4 Goal-driven execution

Turn each task into a verifiable goal:

- "Add validation" → write tests for invalid inputs, then make them pass.
- "Fix the bug" → write a test that reproduces it, then make it pass.
- "Refactor X" → make sure the tests pass before and after.

For multi-step tasks, state a brief plan with a check for each step:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
```

---

## 2. Git, branches, migrations and data

### 2.1 Commits

- Agents never commit: no `git commit` (also `--amend`), `git merge`,
  `git cherry-pick`, `git revert` or any other command that creates
  commits.
- Agents change the files in the working tree and leave them
  uncommitted. At the end of a task they list the changed files, so the
  user can review and commit them. They do not offer to commit.

### 2.2 Branch `main`

- On `main`, writing to the project folder is forbidden. Before any
  change, check the branch (`git branch --show-current`). If it is
  `main`, do not create, edit, move or delete any file in the project
  (no editor writes, shell redirections, `sed -i`, nor commands that
  generate files such as `pip install` in a virtualenv inside the
  project, `makemigrations`, `startapp`, `collectstatic`,
  `compilemessages`, formatters). Stop and ask the user to switch
  branch.
- Files outside the project folder (scratchpad, plan files) are not
  affected.
- Committing on `main` is forbidden. The only changes on `main` are
  merges of `release-*` branches, done by the user.

### 2.3 Migrations

- Agents never apply migrations: no `migrate` in any form (with an app,
  a target, `zero`, `--fake`, `--fake-initial`, `--run-syncdb`), no
  migration operations or DDL run by hand from `manage.py shell`,
  `dbshell` or an SQL client. The rule holds on every database, even
  when the user asks to "proceed". The only exception is the test
  database created by the test runner (section 7).
- An agent may create a migration (`makemigrations` or by hand) and check
  it without applying it: `sqlmigrate <app> <migration>` (prints the
  SQL), `makemigrations --check --dry-run`, `showmigrations`, code review,
  comparison with `information_schema`. Then it tells the user that the
  migration is ready and must be applied by the user.
- A migration contains **only** the operations of the change being made.
  Run `makemigrations <app>` for the app you changed. If it also
  generates operations for models not involved in the change, do not
  keep them: write the migration by hand with only the needed
  operations.
- In legacy code a model may not match its table on purpose: do not fix
  it, and do not create migrations for it, unless the task asks.

### 2.4 Data

- Data in the development database may be unreliable: never rely on it
  to reconstruct the behaviour of the code (read the code instead). Use
  it only to check that code and scripts run.
- Read and write queries on the development database are allowed
  (`SELECT`, ORM reads in `manage.py shell`; `INSERT`, `UPDATE`,
  `DELETE`, `save()`, `create()`, `loaddata`).
- Migrations are not data queries: agents never run them, also when the
  user asks (section 2.3).

---

## 3. Environment and commands

### 3.1 Execution environment

- Every command runs in the execution environment of the project: on
  the machine or in Docker.
- If the section "Execution environment" at the end of this file says
  how the project runs, follow it.
- Otherwise work it out from the project: with a `Dockerfile` and a
  `docker-compose.yml` (or `compose.yaml`) the project probably runs in
  Docker, and the commands run in its container
  (`docker compose exec <service> python manage.py <command>`); without
  them it probably runs on the machine, in its virtualenv (e.g.
  `.venv/bin/python`).
- When in doubt, ask the user which is the execution environment the
  first time a command is needed. Then write the answer in the section
  "Execution environment" at the end of this file (add it if missing),
  so as not to ask again:

  ```markdown
  ## Execution environment

  - Docker, service `app`: `docker compose exec app <command>`.
  ```

  Writing this file follows section 2.2: on `main`, do not write it and
  tell the user.

### 3.2 Dependencies

- Agents never install, update or remove dependencies: no
  `pip install` / `uninstall`, `uv add` / `sync`, `poetry add` /
  `update`, `npm install` / `update`. The user runs them.
- When a task needs a new dependency, or another version of an
  installed one, suggest to the user the command to run, with the tool
  of the project (`pip` + `requirements*.txt`, `uv`, `poetry`, ...; with
  `pip`, also the line to add to the requirements file), and a version
  compatible with the installed framework and packages. Then wait for
  the user to run it.
- If the dependencies are not installed, ask the user to install them.

### 3.3 Configuration

- The values that change from one environment to another (credentials,
  hosts, keys, flags) are read from the environment variables and, when
  a variable is not set, from `.env`: the environment always wins over
  `.env`.
- The values enter the configuration in `settings.py` (with split
  settings, the base module), read with the mechanism the project
  already has (`os.environ`, `django-environ`, `python-decouple`, ...),
  and the code always reads them from `django.conf.settings`. Never read
  `os.environ` or `.env` outside the settings.

### 3.4 Commands

- Use the Python executable the project uses (`python` or `python3`).
- Common commands:
  - `python manage.py runserver`: development server;
  - `python manage.py test`: test suite (or `pytest`, if the project
    uses `pytest-django`);
  - `python manage.py check`: system checks;
  - `python manage.py makemigrations <app>`: creates migrations
    (section 2.3);
  - `python manage.py makemessages -l <locale>`, `compilemessages`:
    translations.

---

## 4. Code style

### 4.1 Formatting

1. Follow PEP 8. If the project configures a formatter or a linter
   (`ruff`, `black`, `flake8`), follow its configuration.

   The formatter runs only on new code: only on the files created in
   the task. In existing files, write the new and changed lines already
   formatted and do not run the formatter on the file: it would change
   lines that are not part of the task (section 1.3).

   Exception: when the user explicitly asks to format a function, a
   class or a file with the coding rules, format exactly that part: a
   file with the formatter; a function or a class by applying the rules
   to it only, leaving the rest of the file as it is.
2. Keep lines within **80 columns**. Split long strings over several
   lines:

   ```python
   msg = "Stored {} records in `{}` "
   msg += "by {} bulks of {} records"
   msg = msg.format(total, table, bulk_cnt, bulk_size)
   ```

3. Build strings with `str.format()` and `{}` placeholders, not with
   f-strings, `%` or concatenation of values:

   ```python
   # Right
   msg = "Missing records in {}: {}".format(table, count)

   # Wrong
   msg = f"Missing records in {table}: {count}"
   msg = "Missing records in %s: %d" % (table, count)
   msg = "Missing records in " + table + ": " + str(count)
   ```

   Exception: raw SQL queries may use a multi-line triple-quoted string,
   with the table names set by `format()` and the values passed as
   parameters with the `%s` placeholders of the database driver (never
   formatted into the string):

   ```python
   query = """SELECT o.*
   FROM {} o
   LEFT JOIN {} p ON p.order_id = o.id
   WHERE o.created_at >= %s
     AND o.created_at < %s
     AND p.order_id IS NULL""".format(orders_table, payments_table)
   cursor.execute(query, [date_from, date_to])
   ```

4. Write function and method calls in the first form that fits within 80
   columns:

   - all on one line:

     ```python
     result = self.do_something(par1, par2)
     ```

   - the arguments on one indented line between the parentheses:

     ```python
     result = self.do_something(
         par1, par2, par3, par4, par5
     )
     ```

   - one argument per line:

     ```python
     result = self.do_something(
         par1,
         par2,
         par3,
         par4,
         par5,
         par6,
         par7,
         par8,
         par9,
     )
     ```

   Never split the arguments over several lines with more than one
   argument per line:

   ```python
   # Wrong
   result = self.do_something(
       par1, par2, par3, par4, par5, par6, par7,
       par8, par9
   )
   ```

### 4.2 Language

Use **English only**, everywhere: class, function and variable names,
comments, docstrings, documentation, tests, `help_text` and
`verbose_name`, migration and log messages, user-facing strings. If the
project uses translations, wrap user-facing strings in `gettext` /
`gettext_lazy` (`_()`). If it does not, as some legacy projects, do not
handle translations: no translation functions and no `.po` files.

---

## 5. Architecture

### 5.1 Base models **(helper)**

- Business models extend a project base model, never Django's
  `models.Model` directly:
  - `BaseModel` (`core/<prefix>_models/base_model.py`): abstract base
    model with common functionality;
  - `BaseModelWithActivityLog`
    (`core/<prefix>_models/base_model_with_activity_log.py`):
    `BaseModel` + change log with `django-auditlog` (every field of
    every concrete subclass is logged, with the user who made the
    change).
- **The user decides the activity log of every model.** When asked to
  create a new **entity** or a new **managed model** (see the
  Glossary), ask the user whether its model needs the activity log
  before writing it, and extend `BaseModelWithActivityLog` only if the
  answer is yes, otherwise `BaseModel`. Never choose by yourself and
  never assume a default, also when the task creates several entities
  or models: ask for each one. The activity log writes a row for every
  change, so models that are already a log are a reason to answer no:
  audit, logging, journals, operations, movements (e.g. a
  `ProductMovement` of a warehouse application, which already records
  the timestamp, the user and the change of quantity of its
  `Product`). Mention it when you ask.
- Switching an existing model between `BaseModel` and
  `BaseModelWithActivityLog` is done only when the user asks.
- `bulk_create()`, `bulk_update()`, `QuerySet.update()`,
  `QuerySet.delete()` and `BulkInsert` do not go through the activity
  log. Use them only for mass operations: every write on a single record
  goes through the model, so that the activity log records it:
  `Product.objects.create(...)`, `product.save()`, `product.delete()`;
  never `bulk_create()`, `BulkInsert`, raw SQL or an `update()` /
  `delete()` on a QuerySet that selects one record.
- Models with `deleted_at` (section 6.1) use soft deletes, as the
  `SoftDeletes` trait of Laravel: they extend `SoftDeletes`
  (`core/<prefix>_models/soft_deletes.py`) before their base model,
  `class Product(SoftDeletes, BaseModel)`. `delete()`, also on a
  QuerySet, sets `deleted_at`, and `objects` hides the deleted rows;
  `objects.with_trashed()` and `objects.only_trashed()` include them,
  `restore()` restores a row, `force_delete()` deletes it.
- Tables without a single primary key use `models.CompositePrimaryKey`
  (Django 5.2 and later).

### 5.2 Logging **(helper)**

- Use the project `Logger`, not `logging`, `print()` or
  `self.stdout.write()` for log messages:

  ```python
  from core.<prefix>_utils.logger import Logger

  Logger.info("Message")
  ```

- `Logger` writes to a daily file and, in the management commands
  (`python manage.py ...`), also to stdout.
- `self.stdout.write()` in a management command is only for the output
  of the command (e.g. a report the user asked for), not for logs.

### 5.3 Jobs: Business Logic + management command

Every long-running task is made of two parts:

- a **Business Logic class**
  (`<app>/<prefix>_services/<domain>/<name>.py`) that contains all the
  logic and accepts all the parameters;
- a **management command** (`<app>/management/commands/<name>.py`) that
  runs it in the terminal.

Rules:

1. Long-running tasks run only through their management command
   (`python manage.py <name>`): no background task or worker (Celery,
   RQ, Django tasks, ...).
2. The management command blocks the terminal and shows the logs in the
   console.
3. The management command and the Business Logic class accept the same
   parameters. When parameters change, change them in both.
4. The management command contains no logic: it reads the parameters,
   instantiates the Business Logic class, runs it and reports the result
   (exit code, `CommandError`). It does not call other commands with
   `call_command()`.
5. To change the logic, change only the Business Logic class.
6. The Business Logic class logs its progress with the `Logger`
   (section 5.2).

```python
# shop/<prefix>_services/products/import_products.py
class ImportProducts:
    def __init__(self, kind, user_id):
        self.kind = kind
        self.user_id = user_id

    def run(self):
        ...


# shop/management/commands/import_products.py
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--kind", required=True)
        parser.add_argument("--user_id", type=int, required=True)

    def handle(self, *args, **options):
        logic = ImportProducts(options["kind"], options["user_id"])
        logic.run()
```

### 5.4 Version **(helper)**

- The version of the project is written only in `.version`, in the
  project root. To release a new version, change only that file.
- Read it with `core.version.get_version()`, or use
  `core.constants.VERSION` / `settings.VERSION`, which come from it.
  Never hardcode the version elsewhere: settings of third-party
  libraries use `VERSION` of the settings, templates receive
  `settings.VERSION` in the context.
- Files that cannot read `.version` (`pyproject.toml`, `package.json`,
  ...) are kept aligned by hand: when `.version` changes, update them
  too.

### 5.5 Naming

- Django REST Framework: `<Model>ViewSet`, `<Model>Serializer`.
- Test modules: `test_<feature>.py`.
- Modules: the name of their class in `snake_case` (section 5.6).

### 5.6 Package layout

Django keeps every kind of component of an app in one module
(`models.py`, `views.py`, `serializers.py`, ...), which grows with the
project. Here every kind of component is a **package** of the app, and
every class is in its own module, as in Java:

```
shop/
    __init__.py
    apps.py
    models.py                    # imports only (rule 6)
    admin.py                     # imports only (rule 6)
    urls.py
    <prefix>_models/
        __init__.py
        category.py              # class Category
        product.py               # class Product
    <prefix>_views/
        __init__.py
        product_view_set.py      # class ProductViewSet
        paginators/
            __init__.py
            product_paginator.py # class ProductPaginator
    <prefix>_serializers/
        __init__.py
        product_serializer.py    # class ProductSerializer
    <prefix>_admin/
        __init__.py
        product_admin.py         # class ProductAdmin
    <prefix>_services/
        __init__.py
        products/
            __init__.py
            import_products.py   # class ImportProducts
    <prefix>_utils/
    <prefix>_exceptions/
    <prefix>_tests/
        __init__.py
        test_product.py
    management/
        __init__.py
        commands/
            __init__.py
            import_products.py   # class Command
    migrations/
```

Rules:

1. **Package names**: `<prefix>_<kind>`, with the kind in the plural:
   `<prefix>_models`, `<prefix>_views`, `<prefix>_serializers`,
   `<prefix>_forms`, `<prefix>_admin`, `<prefix>_services`,
   `<prefix>_utils`, `<prefix>_exceptions`,
   `<prefix>_middlewares`, `<prefix>_signals`, `<prefix>_tests`, ...
   `<prefix>` is the same in every app of the project (e.g.
   `infojuice`). It avoids the clash with the modules that Django looks
   for by name (`models.py` and a `models/` package cannot coexist) and
   with third-party packages.
2. **`__init__.py`**: every package and subpackage has an `__init__.py`,
   empty. No folders without `__init__.py` (namespace packages), and no
   re-exports in `__init__.py`.
3. **One class per module**. The module is named after the class, in
   `snake_case`; outside `<prefix>_models` the class name already ends
   with its kind:
   - `Product` → `<prefix>_models/product.py`;
   - `ProductViewSet` → `<prefix>_views/product_view_set.py`;
   - `ProductSerializer` → `<prefix>_serializers/product_serializer.py`;
   - `DuplicatedProductException` →
     `<prefix>_exceptions/duplicated_product_exception.py`.

   Inner classes (`Meta`, `TextChoices`) and small helpers used only by
   the class of the module stay in its module. Modules of functions
   (utilities) hold the functions of a single purpose.
4. **Subpackages**: when a package grows, group its modules in
   subpackages by topic (e.g. `<prefix>_views/paginators/`,
   `<prefix>_utils/elasticsearch/`), each with its `__init__.py`.
5. **Imports**: import every class from its module, with the absolute
   path:

   ```python
   from shop.<prefix>_models.product import Product
   from shop.<prefix>_serializers.product_serializer import (
       ProductSerializer,
   )
   ```

   Never import from the aggregators (`from shop.models import
   Product`): it causes circular imports. Models that refer to each
   other use the string reference (`models.ForeignKey("shop.Category",
   ...)`).
6. **Modules looked for by name** stay where Django and the libraries
   want them: `apps.py`, `urls.py`, `migrations/`,
   `management/commands/<command>.py` (one command per module),
   `templatetags/`. Those that Django or a library imports to discover
   the components become aggregators with imports only:
   - `models.py` imports every concrete model of `<prefix>_models`:
     Django registers only the models imported when the app is loaded,
     and a model that is not imported gets no migrations;

     ```python
     from shop.<prefix>_models.category import Category  # noqa: F401
     from shop.<prefix>_models.product import Product  # noqa: F401
     ```

   - `admin.py` imports every module of `<prefix>_admin`, where each
     class registers its model with `@admin.register(Model)`:

     ```python
     import shop.<prefix>_admin.product_admin  # noqa: F401
     ```

   Every new model or admin class is added to its aggregator.
7. **Existing code**: classes already in `models.py`, `views.py`,
   `serializers.py`, ... stay where they are: the rule applies to new
   classes. Move an existing class to its package only when the user
   asks. Moving a model does not change its app, table or migrations:
   after the move, `python manage.py makemigrations --check --dry-run`
   must report no changes.

---

## 6. Database

### 6.1 Field order

The fields of every model, and so the columns of its table, follow this
order (declare them in this order in the model):

1. primary key, named `id`, auto-increment (`DEFAULT_AUTO_FIELD`, i.e.
   `BigAutoField` in new projects; do not declare it);
2. `CharField` (and `EmailField`, `SlugField`, `URLField`); `name` and
   `description`, when present, are the first two of them; the other
   ones follow in the order in which they are listed;
3. `TextField`; `note`, when present, is the last of them;
4. fields with `choices` (`TextChoices` / `IntegerChoices`, the Django
   counterpart of `enum`);
5. `UUIDField`;
6. `JSONField`;
7. `DateField` / `DateTimeField` / `TimeField` (other than
   `created_at`, `updated_at`, `deleted_at`);
8. integer fields (`IntegerField`, `BigIntegerField`,
   `PositiveIntegerField`, ...);
9. other numeric fields (`DecimalField`, `FloatField`);
10. `BooleanField`;
11. foreign keys (`ForeignKey`, `OneToOneField`);
12. `created_at` (`auto_now_add=True`);
13. `updated_at` (`auto_now=True`): always `updated_at`, never
    `modified_at`;
14. `deleted_at` (nullable, for soft deletes).

`ManyToManyField` fields have no column: declare them after the foreign
keys.

`created_at`, `updated_at` and `deleted_at` are mandatory in every
model, always the last three fields and in this order. The only
exception is the models of the many-to-many relations (the `through`
models of a `ManyToManyField`). The rule applies to new models: add the
three fields to an existing model only when the user asks.

```python
class Product(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft"
        ACTIVE = "active"

    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    code = models.CharField(max_length=50)
    details = models.TextField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    attributes = models.JSONField(null=True, blank=True)
    available_from = models.DateField(null=True, blank=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
```

`makemigrations` moves the foreign keys to the end of the `fields` of
`CreateModel`, after `created_at`, `updated_at` and `deleted_at`: in the
generated migration, move them back before `created_at`, then check with
`sqlmigrate` and `makemigrations --check --dry-run` (no changes). If
`makemigrations` adds a foreign key with a separate `AddField` (circular
dependencies between models), leave it there.

The order applies to new tables and to new fields. Do not create
migrations only to reorder existing columns.

A new field of an existing table goes in its group in the model.
`migrations.AddField` always adds the column at the end of the table:

- **MySQL / MariaDB**: place the column with `AFTER`. Generate the
  migration, take the SQL of the `AddField` with `sqlmigrate`, add
  `AFTER <column>` and wrap it in `SeparateDatabaseAndState`, so that
  the state of the models stays the same:

  ```python
  operations = [
      migrations.SeparateDatabaseAndState(
          state_operations=[
              migrations.AddField(
                  model_name="product",
                  name="sku",
                  field=models.CharField(
                      max_length=50, null=True, blank=True
                  ),
              ),
          ],
          database_operations=[
              migrations.RunSQL(
                  sql="ALTER TABLE `shop_product` "
                  "ADD COLUMN `sku` varchar(50) NULL AFTER `code`",
                  reverse_sql="ALTER TABLE `shop_product` "
                  "DROP COLUMN `sku`",
              ),
          ],
      ),
  ]
  ```

  Keep every statement that `sqlmigrate` prints for the field (indexes,
  foreign key constraints).

- **PostgreSQL / SQLite**: columns cannot be placed; keep the plain
  `AddField` (the column goes at the end of the table).

### 6.2 Bulk inserts **(helper)**

- Model instances: `Model.objects.bulk_create(objs, batch_size=2000)`.
- Records as dicts (tables without a model, imports): insert them in
  chunks with `BulkInsert` (default chunk: 2000 records; `using` is an
  optional database alias):

  ```python
  from core.<prefix>_utils.bulk_insert import BulkInsert

  BulkInsert("table_name", records, 1000).save()
  ```

  `BulkInsert` writes the records as they are: set `created_at` and
  `updated_at` in each record (section 6.1).

---

## 7. Testing

- Tests are in the `<prefix>_tests` package of each app, one module per
  feature (`test_<feature>.py`), and run with `python manage.py test`
  (or `pytest` with `pytest-django`). An existing `tests.py` or `tests/`
  package stays where it is.
- The test runner creates a separate test database on the same engine
  (`test_<name>`; in memory with SQLite) and applies the migrations to
  it: this is allowed. Never point the tests at the development or
  production database.
- Test names and comments are in English.

---

## 8. Helper classes

| Class | Purpose |
|---|---|
| `core.<prefix>_utils.logger.Logger` | Project logging, console output for management commands |
| `core.<prefix>_models.base_model.BaseModel` | Abstract base model |
| `core.<prefix>_models.base_model_with_activity_log.BaseModelWithActivityLog` | Abstract base model with activity log (django-auditlog) |
| `core.<prefix>_models.soft_deletes.SoftDeletes` | Soft deletes on `deleted_at` |
| `core.<prefix>_utils.bulk_insert.BulkInsert` | Chunked bulk inserts of dict records |
| `core.version.get_version()` | Version of the project, read from `.version` |
| `core.constants` | `APP_NAME`, `VERSION` (from `.version`) |
