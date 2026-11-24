# Laravel Coding Rules

Coding and implementation rules for Laravel projects.

Rules marked **(helper)** use a helper class of the project, listed in
section 8. Names in the examples (tables, classes) are placeholders:
adapt them.

---

## Glossary

- **Entity**: a domain object managed by the system, made of a model,
  its views and its controller. Creating an entity means creating all
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
  generate files such as `composer install`, `npm run build`,
  `./vendor/bin/pint`, `make:*`). Stop and ask the user to switch branch.
- Files outside the project folder (scratchpad, plan files) are not
  affected.
- Committing on `main` is forbidden. The only changes on `main` are
  merges of `release-*` branches, done by the user.

### 2.3 Migrations

- Agents never run migrations: no `migrate`, `migrate:fresh`,
  `migrate:rollback`, `migrate:refresh`, `migrate:reset`, no `up()` /
  `down()` in tinker, no DDL executed by hand. The rule holds on every
  database, even when the user asks to "proceed". The only exception is
  the test database, where the tests run the migrations (section 7).
- An agent may write a migration and check it without running it
  (syntax, code review, comparison with `information_schema`). Then it
  tells the user that the migration is ready and must be run by the user.
- A migration contains **only** the operations of the change being made:
  do not add changes to tables, columns or indexes not involved in it.
- In legacy code a model may not match its table on purpose: do not fix
  it, and do not create migrations for it, unless the task asks.

### 2.4 Data

- Data in the development database may be unreliable: never rely on it
  to reconstruct the behaviour of the code (read the code instead). Use
  it only to check that code and scripts run.
- Read and write queries on the development database are allowed
  (`SELECT`, Eloquent and query builder reads in `tinker`; `INSERT`,
  `UPDATE`, `DELETE`, `save()`, `create()`, `db:seed`).
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
  (`docker compose exec <service> php artisan <command>`, or
  `./vendor/bin/sail artisan <command>` with Laravel Sail); without them
  it probably runs on the machine, with its PHP and Composer.
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
  `composer install` / `update` / `require` / `remove`, `npm install` /
  `update`. The user runs them.
- When a task needs a new dependency, or another version of an
  installed one, suggest to the user the command to run (e.g.
  `composer require vendor/package:^1.2`), with a version compatible
  with the installed framework and packages. Then wait for the user to
  run it.
- If the dependencies are not installed, ask the user to install them.

### 3.3 Configuration

- The values that change from one environment to another (credentials,
  hosts, keys, flags) are read from the environment variables and, when
  a variable is not set, from `.env`: the environment always wins over
  `.env`.
- The values enter the configuration in the files of `config/`
  (`'key' => env('VARIABLE', 'default')`), and the code always reads
  them from there with `config('file.key')`. Never call `env()` outside
  the files of `config/`: with the configuration cached it returns
  `null`.

### 3.4 Commands

- Common commands:
  - `composer dev`: server + queue + logs + vite;
  - `composer test` / `php artisan test`: test suite;
  - `./vendor/bin/pint <file>`: formatter, only on new files
    (section 4.1);
  - `php artisan config:clear`, `cache:clear`, `route:clear`.
- Queue worker in development: `php artisan queue:listen --tries=1`.

---

## 4. Code style

### 4.1 Formatting

1. Follow the Laravel Pint style (`./vendor/bin/pint`, with the
   `pint.json` of the project if present).

   The formatter runs only on new code: only on the files created in
   the task. In existing files, write the new and changed lines already
   formatted and do not run the formatter on the file: it would change
   lines that are not part of the task (section 1.3).

   Exception: when the user explicitly asks to format a function, a
   class or a file with the coding rules, format exactly that part: a
   file with the formatter; a function or a class by applying the rules
   to it only, leaving the rest of the file as it is.
2. Keep lines within **80 columns**.
3. Build strings with `sprintf()` instead of concatenation or
   interpolation:

   ```php
   $msg = sprintf("Missing records in %s: %d", $table, $count);
   ```

   Exception: raw SQL queries may use a multi-line double-quoted string
   with interpolated table names and `?` placeholders for values:

   ```php
   $query = "SELECT o.*
   FROM $orders_table o
   LEFT JOIN $payments_table p ON p.order_id = o.id
   WHERE o.created_at >= ?
     AND o.created_at < ?
     AND p.order_id IS NULL";
   ```

4. Write function and method calls in the first form that fits within 80
   columns:

   - all on one line:

     ```php
     $result = $this->doSomething($par1, $par2);
     ```

   - the arguments on one indented line between the parentheses:

     ```php
     $result = $this->doSomething(
         $par1, $par2, $par3, $par4, $par5
     );
     ```

   - one argument per line:

     ```php
     $result = $this->doSomething(
         $par1,
         $par2,
         $par3,
         $par4,
         $par5,
         $par6,
         $par7,
         $par8,
         $par9
     );
     ```

   Never split the arguments over several lines with more than one
   argument per line:

   ```php
   // Wrong
   $result = $this->doSomething(
       $par1, $par2, $par3, $par4, $par5, $par6, $par7,
       $par8, $par9
   );
   ```

### 4.2 Language

Use **English only**, everywhere: class, method and variable names,
comments, documentation, tests, database comments, migration and log
messages, user-facing strings. If the project uses translations, wrap
user-facing strings in `__()` (`@lang` / `{{ __() }}` in Blade). If
it does not, as some legacy projects, do not handle translations: no
translation functions and no language files.

---

## 5. Architecture

### 5.1 Base models **(helper)**

- Business models extend a project base model, never Laravel's `Model`
  directly:
  - `BaseModel`: base model with common functionality;
  - `BaseModelWithActivityLog`: `BaseModel` + Spatie activity logging.
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
- The query builder (`DB::table()`), `insert()`, the mass `update()` and
  `delete()` on a query (e.g. `Product::where(...)->update(...)`) and
  `BulkInsert` do not go through the activity log. Use them only for
  mass operations: every write on a single record goes through the
  model, so that the activity log records it: `Product::create(...)`,
  `$product->save()`, `$product->update([...])`, `$product->delete()`;
  never `insert()`, the query builder or an update or delete on a query
  that selects one record.
- Models with `deleted_at` (section 6.1) use soft deletes: `use
  Illuminate\Database\Eloquent\SoftDeletes;` and `use SoftDeletes;` in
  the model. `delete()` sets `deleted_at` and the queries hide the
  deleted rows; `withTrashed()` and `onlyTrashed()` include them,
  `restore()` restores a row, `forceDelete()` deletes it.
- Tables without a single primary key use
  `thiagoprz/eloquent-composite-key`.

### 5.2 Logging **(helper)**

- Use the project `Logger` facade, not Laravel's `Log`:

  ```php
  use Logger;
  Logger::info("Message");
  ```

- `Logger` writes to stdout when the `console` channel is in
  `logging.channels.stack.channels` (used by artisan commands).

### 5.3 Jobs: Business Logic + Job + artisan command

Every long-running task is made of three classes:

- a **Business Logic class** (e.g. `app/Services/<Domain>/`) that
  contains all the logic and accepts all the parameters;
- a **Job** (`app/Jobs/`) that runs it in background;
- an **artisan command** (`app/Console/Commands/`) that runs it in the
  terminal.

Rules:

1. Every Job has a matching artisan command.
2. The artisan command blocks the terminal and shows the logs in the
   console.
3. The Job runs in background and periodically updates its progress in
   the queue monitor.
4. The Job and the artisan command accept the same parameters.
5. The Business Logic class receives all the parameters and is built and
   run in the same way by the Job and by the command. The Job does not
   call the command with `Artisan::call()`, and the command does not
   dispatch the Job: both use the Business Logic class directly.
6. To change the logic, change only the Business Logic class. The Job and
   the command contain no logic: they read the parameters, build the
   Business Logic class, run it and report the result (notification,
   exit code).
7. When parameters change, change them in both the Job and the command,
   then pass them to the Business Logic class.

Progress: the Job passes its job id to the Business Logic class, which
loads the queue monitor record (e.g. `QueueMonitor` from a
queue-monitor package) and updates `progress` and `exception_message`.
Without a job id (artisan command) the Business Logic class only logs.

```php
// Job
public function handle(): void {
    $logic = new ImportSomething($this->type, $this->user_id);
    $logic->setJobId($this->job->getJobId());
    $logic->run();
}

// Artisan command
public function handle() {
    $logic = new ImportSomething(
        $this->option('type'), $this->option('user_id')
    );
    $logic->run();
    return Command::SUCCESS;
}
```

### 5.5 Naming

- Parts of an entity (Glossary): controller `<Model>Controller`, views
  in `resources/views/<models>/` (e.g.
  `resources/views/products/index.blade.php`).
- Test classes: `<Feature>Test` (`tests/Feature/<Feature>Test.php`,
  `tests/Unit/<Feature>Test.php`).
- Files: the name of their class (section 5.6).

### 5.6 Code structure

1. Follow the standard structure of Laravel (PSR-4): every class is in
   its own file, named after the class, in the folder of its kind
   (`app/Models/`, `app/Http/Controllers/`, `app/Http/Requests/`,
   `app/Jobs/`, `app/Console/Commands/`, ...).
2. Helpers and business logic go in a **dedicated class for the
   specific activity**, never in global helper functions nor in a
   generic class that collects unrelated methods:
   - business logic: `app/Services/<Domain>/<Activity>.php` (e.g.
     `app/Services/Products/ImportProducts.php`);
   - helpers: `app/Classes/<Activity>.php` (e.g.
     `app/Classes/CsvExporter.php`).

   Controllers, models, Jobs and artisan commands use these classes:
   they do not contain the logic themselves.
3. When a folder grows, group its classes in subfolders by topic, with
   the namespace that matches the folder (e.g.
   `app/Services/Products/`).
4. Existing code stays where it is: the rule applies to new classes.
   Move an existing class or function only when the user asks.

---

## 6. Database

### 6.1 Column order

Columns of every table follow this order:

1. primary key, named `id`, unsigned, auto-increment (`$table->id()`);
2. `varchar` columns (`string`); `name` and `description`, when present,
   are the second and third column of the table; the other `varchar`
   columns follow in the order in which they are listed;
3. `text` / `longText` columns; `note`, when present, is the last of
   them;
4. `enum` columns;
5. `uuid` columns;
6. `json` columns;
7. `date` / `datetime` / `timestamp` columns (other than `created_at`,
   `updated_at`, `deleted_at`);
8. integer columns;
9. other numeric columns (decimal, float, double, ...);
10. boolean columns;
11. foreign keys (`foreignId()`);
12. `created_at`;
13. `updated_at`;
14. `deleted_at`.

`created_at`, `updated_at` and `deleted_at` are mandatory in every
table, always the last three columns and in this order
(`$table->timestamps()` then `$table->softDeletes()`). The only
exception is the pivot tables of the many-to-many relations. The rule
applies to new tables: add the three columns to an existing table only
when the user asks.

```php
Schema::create('products', function (Blueprint $table) {
    $table->id();
    $table->string('name');
    $table->string('description')->nullable();
    $table->string('code');
    $table->text('details')->nullable();
    $table->text('note')->nullable();
    $table->enum('status', ['draft', 'active'])->default('draft');
    $table->uuid('uuid')->unique();
    $table->json('attributes')->nullable();
    $table->date('available_from')->nullable();
    $table->integer('quantity');
    $table->decimal('price', 10, 2);
    $table->boolean('active')->default(true);
    $table->foreignId('category_id')->constrained();
    $table->timestamps();
    $table->softDeletes();
});
```

A migration that adds columns to an existing table places each column in
its group with `->after()`. A new `varchar` goes after the last `varchar`
and before the first `text` / `longText` column:

```php
Schema::table('products', function (Blueprint $table) {
    $table->string('sku')->nullable()->after('code');
    $table->decimal('weight', 8, 2)->nullable()->after('price');
});
```

`->after()` works only on **MySQL / MariaDB**. On **PostgreSQL /
SQLite** columns cannot be placed: leave `->after()` out of the
migration, and the new column goes at the end of the table.

### 6.2 Bulk inserts **(helper)**

Insert large datasets in chunks with `BulkInsert` (default chunk: 2000
records; the last argument is an optional connection name):

```php
use App\Classes\BulkInsert;

(new BulkInsert('table_name', $records, 1000))->save();
```

`BulkInsert` writes the records as they are: set `created_at` and
`updated_at` in each record (section 6.1).

---

## 7. Testing

- Tests are in `tests/Feature/` and `tests/Unit/`, configured in
  `phpunit.xml`.
- Test database: a separate database on the same engine as the project,
  set in `phpunit.xml` (or `.env.testing`): the same `DB_CONNECTION`,
  and as `DB_DATABASE` a database used only by the tests (`:memory:`
  with SQLite). The user creates it. The tests run the migrations on
  it: this is allowed. Never point the tests at the development or
  production database.
- Test names and comments are in English.

---

## 8. Helper classes

| Class | Purpose |
|---|---|
| `App\Classes\Logger` + `App\Facades\Logger` (alias `Logger`) | Project logging, console output for artisan commands |
| `App\Models\BaseModel`, `App\Models\BaseModelWithActivityLog` | Base models (Spatie activity log) |
| `App\Classes\BulkInsert` | Chunked bulk inserts |
