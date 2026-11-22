<?php
namespace App\Classes;

use Monolog\Processor\IntrospectionProcessor;
use Monolog\Handler\StreamHandler;
use Monolog\Handler\RotatingFileHandler;
use Monolog\Formatter\LineFormatter;

class Logger {

    protected static $loggers = [];

    public static function init($APP_NAME = null, $name = 'main') {

        /*
         * LOGGING ON FILE
         */
        // TODO move to .env
        $log_file = storage_path('logs/__PROJECT_NAME__.log');

        $log_level = "DEBUG";
        $stack_channels = config('logging.channels.stack.channels', []);
        foreach ($stack_channels as $channel) {
            if ($channel == 'console') {
                continue;
            }

            $log_level = $channel
                ? config("logging.channels.$channel.level", 'DEBUG')
                : 'DEBUG';
        }

        $log_introspection = true;
        if (!$log_file || empty($log_file)) {
           $pathinfo = pathinfo(__DIR__);
           $log_file = "%s.log";
           $log_file = sprintf($log_file, $pathinfo['filename']);
        }
        // Log level setting
        if (!$log_level || empty($log_level)) {
           $log_level = "WARNING";
        }
        switch (strtoupper($log_level)) {
           case "DEBUG":
           default:
               $log_level = \Monolog\Logger::DEBUG;
           break;
           case "INFO":
               $log_level = \Monolog\Logger::INFO;
           break;
           case "NOTICE":
               $log_level = \Monolog\Logger::NOTICE;
           break;
           case "WARNING":
               $log_level = \Monolog\Logger::WARNING;
           break;
           case "ERROR":
               $log_level = \Monolog\Logger::ERROR;
           break;
           case "CRITICAL":
               $log_level = \Monolog\Logger::CRITICAL;
           break;
           case "ALERT":
               $log_level = \Monolog\Logger::ALERT;
           break;
           case "EMERGENCY":
               $log_level = \Monolog\Logger::EMERGENCY;
           break;
        }
        // Log introspection setting
        if ($log_introspection === true || $log_introspection == 1) {
           $log_introspection = true;
        }
        else {
           $log_introspection = false;
        }
        // Log instance
        $logger_name = "%s/%d";
        $my_pid = getmypid();
        $logger_name = sprintf($logger_name, $APP_NAME, $my_pid);
        global $logger;
        $logger = new \Monolog\Logger($logger_name);

        $dateFormat = "Y-m-d H:i:s";
        $output = "[%datetime%] %channel%.%level_name%: %message% %context% %extra%\n";
        // finally, create a formatter
        $formatter = new LineFormatter($output, $dateFormat);

        // Create a rotating handler on file
        $stream = new RotatingFileHandler($log_file, 0, $log_level);
        $stream->setFormatter($formatter);
        $logger->pushHandler($stream);

        // Create a console stream handler
        $channels = config('logging.channels.stack.channels');
        if (in_array('console', $channels)) {
            $console_log_level = config(
                "logging.channels.console.level", 'DEBUG'
            );
            $formatter = new LineFormatter($output, $dateFormat, TRUE, TRUE);
            $console = new StreamHandler('php://stdout', $console_log_level);

            if (class_exists("\Bramus\Monolog\Formatter\ColoredLineFormatter")) {
                $color = new \Bramus\Monolog\Formatter\ColoredLineFormatter();
                $console->setFormatter($color);
            }
            $logger->pushHandler($console);
        }
        \Monolog\ErrorHandler::register($logger);
        if ($log_introspection) {
            $skip = [
                'Logger', 'Facade'
            ];
            $processor = new IntrospectionProcessor($log_level, $skip);
            $logger->pushProcessor($processor);
        }
        self::$loggers[$name] = $logger;
    }

    public static function debug($msg, $name = 'main') {
        if (!isset(self::$loggers[$name])) {
            self::init(APP_NAME, $name);
        }
        self::$loggers[$name]->debug($msg);
    }

    public static function info($msg, $name = 'main') {
        if (!isset(self::$loggers[$name])) {
            self::init(APP_NAME, $name);
        }
        self::$loggers[$name]->info($msg);
    }

    public static function warning($msg, $name = 'main') {
        if (!isset(self::$loggers[$name])) {
            self::init(APP_NAME, $name);
        }
        self::$loggers[$name]->warning($msg);
    }

    public static function error($msg, $name = 'main') {
        if (!isset(self::$loggers[$name])) {
            self::init(APP_NAME, $name);
        }
        self::$loggers[$name]->error($msg);
    }

    public static function alert($msg, $name = 'main') {
        if (!isset(self::$loggers[$name])) {
            self::init(APP_NAME, $name);
        }
        self::$loggers[$name]->alert($msg);
    }

    public static function sql($query, $name = 'main') {
        if (!isset(self::$loggers[$name])) {
            self::init(APP_NAME, $name);
        }

        $sql = $query->toSql();
        $bindings = $query->getBindings();

        // Replace the '?' placeholders with the actual values
        foreach ($bindings as $binding) {
            $sql = preg_replace('/\?/', "'$binding'", $sql, 1);
        }

        self::$loggers[$name]->debug($sql);

    }
}
