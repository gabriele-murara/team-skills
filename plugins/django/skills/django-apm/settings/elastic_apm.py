# Snippet for the base settings module (the one that defines
# INSTALLED_APPS and MIDDLEWARE): it is not a module of the project.
# Move `import socket` to the imports of the settings module, put
# APM_ACTIVE near the other general settings, and the rest after
# INSTALLED_APPS and MIDDLEWARE. Replace __SERVICE_NAME__ and adapt
# TRANSACTIONS_IGNORE_URLS (SKILL.md, section 3).
import socket

APM_ACTIVE = env.bool('APM_ACTIVE', default=False)

ELASTIC_APM = {
    # if True, APM will send no messages to the server.
    'DISABLE_SEND': not APM_ACTIVE,
    # set required service name. Allowed characters: a-z, A-Z, 0-9, -, _, space
    # You can set this value in host environment with `ELASTIC_APM_<var>` or
    # in `.env` file with just `APM_<var>`
    'SERVICE_NAME': env.str(
        'APM_SERVICE_NAME',
        default=env.str('ELASTIC_APM_SERVICE_NAME', '__SERVICE_NAME__')
    ),
    'HOSTNAME': env.str(
        'APM_HOSTNAME',
        default=env.str('ELASTIC_APM_HOSTNAME', socket.gethostname())
    ),
    # set custom APM Server URL
    'SERVER_URL': env.str('ELASTIC_APM_SERVER_URL', default=None),
    'ENABLED': APM_ACTIVE,
    # Required when Django DEBUG=True, otherwise the middleware skips tracing
    'DEBUG': env.bool('ELASTIC_APM_DEBUG', default=False),
    # Sample rate for transactions (0.0 to 1.0). Default 0.1 = 10% of requests.
    # Use 1.0 only for debugging, not in production.
    'TRANSACTION_SAMPLE_RATE': env.float(
        'APM_TRANSACTION_SAMPLE_RATE', default=0.1
    ),
    # URLs to ignore (not traced). Supports wildcards.
    'TRANSACTIONS_IGNORE_URLS': [
        '/health/*',
        '/health',
        '/version*',
    ],
    # Minimum duration for collecting stack traces on spans.
    # Higher values reduce overhead. Use '0ms' to always collect, '-1ms' to
    # never collect.
    'SPAN_STACK_TRACE_MIN_DURATION': env.str(
        'APM_SPAN_STACK_TRACE_MIN_DURATION', default='100ms'
    ),
}

# Add SECRET_TOKEN only if defined (optional, used if APM Server requires auth)
_apm_secret_token = env.str('APM_SECRET_TOKEN', default=None)
if _apm_secret_token:
    ELASTIC_APM['SECRET_TOKEN'] = _apm_secret_token

# If you are going to modify APM_ACTIVE from a new settings file that
# extends the default one, you need to copy these lines:
if APM_ACTIVE:
    # add this app just if needed or the agent will spam connection errors
    INSTALLED_APPS.append('elasticapm.contrib.django')
    MIDDLEWARE.insert(
        0, 'elasticapm.contrib.django.middleware.TracingMiddleware'
    )
else:
    # remove the middleware, which actually spams messages on the net
    if 'elasticapm.contrib.django.middleware.TracingMiddleware' in MIDDLEWARE:
        MIDDLEWARE.remove(
            'elasticapm.contrib.django.middleware.TracingMiddleware'
        )
    if 'elasticapm.contrib.django' in INSTALLED_APPS:
        INSTALLED_APPS.remove('elasticapm.contrib.django')

# One flag for every process without HTTP that is traced (SKILL.md,
# section 3.3). Remove it if no process is traced.
# Trace every run of the importer as an APM transaction.
# Used only when APM_ACTIVE is True.
APM_IMPORTER_ACTIVE = env.bool('APM_IMPORTER_ACTIVE', default=False)
