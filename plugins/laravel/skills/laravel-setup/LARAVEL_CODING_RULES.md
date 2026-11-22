# Laravel Coding Rules

Coding and implementation rules for Laravel projects.

Rules marked **(helper)** use a helper class of the project, listed in
section 8. Names in the examples (tables, classes) are placeholders:
adapt them.

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
- Match the existing style, even if you would do it differently.
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

## 2. Git, branches and migrations

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
  database, even when the user asks to "proceed".
- An agent may write a migration and check it without running it
  (syntax, code review, comparison with `information_schema`). Then it
  tells the user that the migration is ready and must be run by the user.

### 2.4 Development database

- Data in the development database may be unreliable: use it to check
  that code and scripts run, not to draw conclusions about the data.

---

## 3. Environment and commands

- Common commands:
  - `composer dev`: server + queue + logs + vite;
  - `composer test` / `php artisan test`: test suite;
  - `./vendor/bin/pint`: formatter;
  - `php artisan config:clear`, `cache:clear`, `route:clear`.
- Queue worker in development: `php artisan queue:listen --tries=1`.

---

## 4. Code style

### 4.1 Formatting

1. Follow Laravel Pint formatting (`./vendor/bin/pint`).
2. Keep lines within **80 columns**.
3. Build strings with `sprintf()` instead of concatenation or
   interpolation:

   ```php
   Logger::info(sprintf("Missing records in %s: %d", $table, $count));
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
messages, user-facing strings.

---

## 5. Architecture

### 5.1 Base models **(helper)**

- Business models extend a project base model, never Laravel's `Model`
  directly:
  - `BaseModel`: base model with common functionality;
  - `BaseModelWithActivityLog`: `BaseModel` + Spatie activity logging.
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

### 6.2 Bulk inserts **(helper)**

Insert large datasets in chunks with `BulkInsert` (default chunk: 2000
records; the last argument is an optional connection name):

```php
use App\Classes\BulkInsert;

(new BulkInsert('table_name', $records, 1000))->save();
```

---

## 7. Testing

- Tests are in `tests/Feature/` and `tests/Unit/`, configured in
  `phpunit.xml`.
- Test database: SQLite `:memory:`.
- Test names and comments are in English.

---

## 8. Helper classes

| Class | Purpose |
|---|---|
| `App\Classes\Logger` + `App\Facades\Logger` (alias `Logger`) | Project logging, console output for artisan commands |
| `App\Models\BaseModel`, `App\Models\BaseModelWithActivityLog` | Base models (Spatie activity log) |
| `App\Classes\BulkInsert` | Chunked bulk inserts |
