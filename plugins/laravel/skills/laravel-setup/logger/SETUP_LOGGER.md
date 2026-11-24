# Logger setup

Instructions for an agent that sets up a Laravel project. The project must
log through the `Logger` facade described here, not through Laravel's
`Log` (see `../LARAVEL_CODING_RULES.md`, section 5.2).

Reference files in this folder:

| File | Target in the project |
|---|---|
| `Logger.php` | `app/Classes/Logger.php` |
| `LoggerFacade.php` | `app/Facades/Logger.php` |
| `aliases.php` | `app/Helpers/aliases.php` |

Before writing any file, follow the rules in
`../LARAVEL_CODING_RULES.md`, section 2: check the branch (never write on
`main`) and never commit.

---

## 1. Required configuration

The Logger is correctly set up when **all** the points below hold.

1. **Class** `App\Classes\Logger` (`app/Classes/Logger.php`), with the
   same behaviour as `Logger.php` in this folder:
   - static methods `debug`, `info`, `warning`, `error`, `alert`
     (`$msg`, `$name = 'main'`) and `sql($query)`, which logs an Eloquent
     or query builder query with the bindings replaced;
   - lazy initialization on first use with `init(APP_NAME, $name)`, one
     Monolog logger per `$name`;
   - Monolog logger named `<APP_NAME>/<pid>`;
   - `RotatingFileHandler` (daily files, no limit) on
     `storage/logs/<project>.log`;
   - file log level taken from the `level` of the non-`console` channels
     in `logging.channels.stack.channels` (default `DEBUG`);
   - format `[%datetime%] %channel%.%level_name%: %message% %context%
     %extra%` with date `Y-m-d H:i:s`;
   - stdout `StreamHandler` only when `console` is in
     `logging.channels.stack.channels`, with level
     `logging.channels.console.level`, and
     `Bramus\Monolog\Formatter\ColoredLineFormatter` when available;
   - `Monolog\ErrorHandler::register()`;
   - `IntrospectionProcessor` that skips the `Logger` and `Facade`
     frames.
2. **Facade** `App\Facades\Logger` (`app/Facades/Logger.php`) with
   accessor `logger.custom`.
3. **Binding** in `App\Providers\AppServiceProvider::register()`:

   ```php
   use App\Classes\Logger;

   $this->app->singleton('logger.custom', function ($app) {
       return new Logger();
   });
   ```

4. **Global alias** `Logger`: `app/Helpers/aliases.php` contains
   `class_alias(\App\Facades\Logger::class, 'Logger');` and is loaded by
   Composer:

   ```json
   "autoload": {
       "files": [
           "app/Helpers/aliases.php"
       ]
   }
   ```

5. **Constant `APP_NAME`**, used by the Logger as the logger name:
   `bootstrap/constants.php` defines it and `bootstrap/app.php` loads it
   at the top with `require_once __DIR__.'/constants.php';`:

   ```php
   <?php

   const APP_NAME = '<ProjectName>';
   const VERSION = '<version>';
   ```

6. **Channels** in `config/logging.php`: the `stack` channel adds
   `console` when running in the terminal, and the `console` channel
   writes to stdout:

   ```php
   'stack' => [
       'driver' => 'stack',
       'channels' => array_values(array_filter(array_merge(
           explode(',', env('LOG_STACK', 'single')),
           app()->runningInConsole() ? ['console'] : []
       ))),
       'ignore_exceptions' => false,
   ],

   'console' => [
       'driver' => 'monolog',
       'handler' => Monolog\Handler\StreamHandler::class,
       'with' => [
           'stream' => 'php://stdout',
       ],
       'level' => env('CONSOLE_LOG_LEVEL', 'debug'),
   ],
   ```

7. **Environment**: `.env` and `.env.example` contain:

   ```
   LOG_CHANNEL=stack
   LOG_STACK=single
   LOG_LEVEL=debug
   CONSOLE_LOG_LEVEL=debug
   ```

8. **Package** (optional, for colored console output):
   `bramus/monolog-colored-line-formatter`.

---

## 2. Procedure

### 2.1 Check

Look for an existing Logger in the project:

- `app/Classes/Logger.php`, `app/Facades/Logger.php`;
- any other class or facade named `Logger`
  (`grep -rn "class Logger" app`);
- the `logger.custom` binding, the `Logger` alias, `APP_NAME`, the
  `stack`/`console` channels.

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

1. Copy `Logger.php` to `app/Classes/Logger.php` and replace
   `__PROJECT_NAME__` with the project name in lowercase (e.g.
   `storage/logs/myproject.log`).
2. Copy `LoggerFacade.php` to `app/Facades/Logger.php`.
3. Copy `aliases.php` to `app/Helpers/aliases.php` and add it to
   `autoload.files` in `composer.json`. If `aliases.php` already exists,
   add only the `class_alias` line.
4. Register the `logger.custom` singleton in `AppServiceProvider`
   (section 1, point 3).
5. Make sure `bootstrap/constants.php` defines `APP_NAME` and is loaded
   in `bootstrap/app.php`: see `../SKILL.md`, section 4, component B.
6. Update the `stack` and `console` channels in `config/logging.php`
   (section 1, point 6), keeping the other channels unchanged. Keep the
   existing expression of the `stack` channels (Laravel 11:
   `explode(',', env('LOG_STACK', 'single'))`, Laravel 12: the same with
   a `(string)` cast, or a custom one) and wrap it in
   `array_values(array_filter(array_merge(<expression>, ...)))` to add
   `console` when running in the terminal.
7. Add the variables of section 1, point 7 to `.env.example` and, if
   present, to `.env`.
8. Ask the user whether they want
   `bramus/monolog-colored-line-formatter` (the Logger works without
   it). If so, install it as in `../SKILL.md`, section 4
   (Dependencies).
9. Run `composer dump-autoload`.

### 2.4 Verify

1. `php artisan tinker --execute="Logger::info('Logger test');"`:
   the message appears on stdout and in
   `storage/logs/<project>-<YYYY-MM-DD>.log`.
2. The log line contains the file and line of the caller (introspection),
   not `Logger.php`.
3. In a web request (no console) the message is written only to the
   file.

At the end, list the files created or changed so the user can review and
commit them.
