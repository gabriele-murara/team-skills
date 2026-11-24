import logging
import os
import sys
from datetime import date

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

from core.constants import APP_NAME

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "[%(asctime)s] {}/%(process)d.%(levelname)s: %(message)s"
LOG_FORMAT += " (%(pathname)s:%(lineno)d %(funcName)s)"


def running_in_console():
    """
    True for the management commands (python manage.py ...,
    django-admin ..., python -m django ...).
    """
    script = sys.argv[0] if sys.argv else ""
    if os.path.basename(script) in ("manage.py", "django-admin"):
        return True
    return script.endswith(os.path.join("django", "__main__.py"))


def get_level(name, default="DEBUG"):
    level = logging.getLevelName(str(name or default).upper())
    return level if isinstance(level, int) else logging.DEBUG


class DailyFileHandler(logging.FileHandler):
    """
    Writes to <name>-YYYY-MM-DD.log and switches file when the day
    changes. It never renames files (unlike TimedRotatingFileHandler), so
    several processes can write to the same log. Old files are kept.
    """

    def __init__(self, filename, level):
        self.base, self.ext = os.path.splitext(filename)
        self.day = date.today()
        super().__init__(self.day_filename(), delay=True)
        self.setLevel(level)

    def day_filename(self):
        return "{}-{}{}".format(self.base, self.day.isoformat(), self.ext)

    def emit(self, record):
        today = date.today()
        if today != self.day:
            self.day = today
            self.close()
            self.baseFilename = os.path.abspath(self.day_filename())
        super().emit(record)


class Logger:
    """
    Project logger. Usage:

        from core.__PREFIX___utils.logger import Logger
        Logger.info("Message")

    Writes to a daily file and, in the management commands, to stdout.
    """

    loggers = {}

    @classmethod
    def init(cls, app_name=APP_NAME, name="main"):
        log_file = getattr(settings, "LOG_FILE", None)
        if not log_file:
            log_file = os.path.join(
                settings.BASE_DIR, "logs", "{}.log".format(app_name.lower())
            )
        log_dir = os.path.dirname(os.path.abspath(log_file))
        os.makedirs(log_dir, exist_ok=True)
        log_level = get_level(getattr(settings, "LOG_LEVEL", "DEBUG"))

        logger = logging.getLogger("{}.{}".format(app_name, name))
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

        log_format = LOG_FORMAT.format(app_name)
        formatter = logging.Formatter(log_format, DATE_FORMAT)

        # Daily file
        file_handler = DailyFileHandler(str(log_file), log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console, only in the management commands
        if running_in_console():
            console_level = get_level(
                getattr(settings, "CONSOLE_LOG_LEVEL", "DEBUG")
            )
            console = logging.StreamHandler(sys.stdout)
            console.setLevel(console_level)
            console.setFormatter(cls.console_formatter(log_format))
            logger.addHandler(console)

        cls.register_excepthook(logger)
        cls.loggers[name] = logger
        return logger

    @staticmethod
    def console_formatter(log_format):
        try:
            import colorlog
        except ImportError:
            return logging.Formatter(log_format, DATE_FORMAT)
        return colorlog.ColoredFormatter(
            "%(log_color)s" + log_format, DATE_FORMAT
        )

    @staticmethod
    def register_excepthook(logger):
        """
        Logs the uncaught exceptions, then calls the previous hook.
        """
        if getattr(sys.excepthook, "project_logger", False):
            return
        previous_hook = sys.excepthook

        def excepthook(exc_type, exc, traceback):
            if not issubclass(exc_type, KeyboardInterrupt):
                logger.critical(
                    "Uncaught exception", exc_info=(exc_type, exc, traceback)
                )
            previous_hook(exc_type, exc, traceback)

        excepthook.project_logger = True
        sys.excepthook = excepthook

    @classmethod
    def get(cls, name="main"):
        if name not in cls.loggers:
            cls.init(APP_NAME, name)
        return cls.loggers[name]

    # stacklevel=2: the log line shows the caller, not this class

    @classmethod
    def debug(cls, msg, name="main"):
        cls.get(name).debug(msg, stacklevel=2)

    @classmethod
    def info(cls, msg, name="main"):
        cls.get(name).info(msg, stacklevel=2)

    @classmethod
    def warning(cls, msg, name="main"):
        cls.get(name).warning(msg, stacklevel=2)

    @classmethod
    def error(cls, msg, name="main"):
        cls.get(name).error(msg, stacklevel=2)

    @classmethod
    def alert(cls, msg, name="main"):
        cls.get(name).critical(msg, stacklevel=2)

    @classmethod
    def sql(cls, queryset, name="main"):
        """
        Logs the SQL of a QuerySet (or Query) with the parameters
        replaced.
        """
        using = getattr(queryset, "db", DEFAULT_DB_ALIAS)
        query = getattr(queryset, "query", queryset)
        sql, params = query.get_compiler(using).as_sql()
        # as_sql() uses %s placeholders and escapes literal % as %%
        sql = sql % tuple("'{}'".format(param) for param in params)
        cls.get(name).debug(sql, stacklevel=2)
