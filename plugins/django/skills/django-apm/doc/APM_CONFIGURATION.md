# Elastic APM configuration

__PROJECT_NAME__ can send performance data (HTTP requests, database queries, errors) to an Elastic APM Server, viewed in Kibana (Observability > APM). APM is optional and disabled by default.

## Prerequisites

- An Elastic APM Server reachable from the application, and its secret token if the server requires authentication.
- The `elastic-apm` 6.x agent, installed with the project dependencies.

## Environment variables

| Variable | Default | Required | Notes |
|---|---|---|---|
| `APM_ACTIVE` | `false` | Yes, to enable APM | Adds the `elasticapm` app and middleware; with `false` nothing is sent |
| `ELASTIC_APM_SERVER_URL` | none | Yes, with `APM_ACTIVE=true` | URL of the APM Server, e.g. `http://apm-server:8200` |
| `APM_SECRET_TOKEN` | none | Only if the server requires it | Sent only when not empty |
| `APM_SERVICE_NAME` | `__SERVICE_NAME__` | No | Name of the service in Kibana; also `ELASTIC_APM_SERVICE_NAME`. Use a different name for every service (API, importer, worker) |
| `APM_HOSTNAME` | host name | No | Also `ELASTIC_APM_HOSTNAME` |
| `ELASTIC_APM_DEBUG` | `false` | No | Must be `true` when Django runs with `DEBUG=True`, otherwise the middleware does not trace. Development only |
| `APM_TRANSACTION_SAMPLE_RATE` | `0.1` | No | Fraction of the requests that are traced (0.0 to 1.0). Use `1.0` only for tests |
| `APM_SPAN_STACK_TRACE_MIN_DURATION` | `100ms` | No | Minimum span duration to collect stack traces; `0ms` always, `-1ms` never |
__PROCESS_FLAG_ROWS__

URLs not traced: __IGNORED_URLS__.

Docker Compose: a variable interpolated in `docker-compose.yml` (`${APM_SECRET_TOKEN}`) but not defined arrives as an empty string. The settings ignore an empty secret token; leave `ELASTIC_APM_SERVER_URL` commented out instead of empty.

## Process monitoring

HTTP requests are traced by the `elasticapm` middleware. __PROCESS_SECTION__

## Application server

__SERVER_SECTION__

## Check the configuration

```bash
__CHECK_APM_COMMAND__
```

The command shows the configuration (with the secret token masked), checks that the APM Server is reachable and that the token is accepted. Expected result with APM enabled: `Server reachability: OK` and `Authentication: OK`.

## Troubleshooting

| Symptom | Cause | Solution |
|---|---|---|
| No transactions in Kibana in development | Django `DEBUG=True` and `ELASTIC_APM_DEBUG=false` | `ELASTIC_APM_DEBUG=true`, development only |
| Few transactions in Kibana | `APM_TRANSACTION_SAMPLE_RATE` is 0.1 by default | `APM_TRANSACTION_SAMPLE_RATE=1.0`, for tests only |
| `Configuration error: value for SERVER_URL is required` | `APM_ACTIVE=true` without `ELASTIC_APM_SERVER_URL` | Set the URL of the APM Server |
| `Authentication failed - check SECRET_TOKEN` | Wrong or missing token | Set `APM_SECRET_TOKEN` |
| Code changes not visible | The application server does not reload the code | Restart the service or the container |
| Unstable workers or missing data | Agent initialized before the fork of the workers | See "Application server" |

## References

- Elastic APM Python agent, Django support: https://www.elastic.co/guide/en/apm/agent/python/current/django-support.html
- Agent configuration options: https://www.elastic.co/guide/en/apm/agent/python/current/configuration.html
