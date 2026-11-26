"""
Management command to check Elastic APM connection.
"""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand

# One entry for every flag of the processes without HTTP that are traced
# (APM_<PROCESS>_ACTIVE). Empty list if no process is traced.
PROCESS_FLAGS = ['APM_IMPORTER_ACTIVE']


class Command(BaseCommand):
    """
    Verifies Elastic APM configuration and connection.
    """

    help = 'Check Elastic APM connection and display configuration'

    def handle(self, *args, **options):
        out = self.stdout.write
        success = self.style.SUCCESS
        error = self.style.ERROR
        warning = self.style.WARNING

        out("\nElastic APM Configuration Check\n")

        # Get APM configuration
        apm_active = getattr(settings, 'APM_ACTIVE', False)
        elastic_apm = getattr(settings, 'ELASTIC_APM', {})

        # Display configuration
        out("APM Configuration")
        rows = [("APM_ACTIVE", apm_active)]
        for flag in PROCESS_FLAGS:
            rows.append((flag, getattr(settings, flag, False)))
        for key in ['ENABLED', 'DISABLE_SEND', 'SERVICE_NAME', 'HOSTNAME',
                    'SERVER_URL', 'DEBUG']:
            rows.append((key, elastic_apm.get(key, 'N/A')))
        secret_token = elastic_apm.get('SECRET_TOKEN')
        if secret_token:
            masked_token = "{}***".format(secret_token[:4])
        else:
            masked_token = "Not set"
        rows.append(("SECRET_TOKEN", masked_token))

        # Performance tuning settings
        rows.append((
            "TRANSACTION_SAMPLE_RATE",
            elastic_apm.get('TRANSACTION_SAMPLE_RATE', 'N/A'),
        ))
        ignore_urls = elastic_apm.get('TRANSACTIONS_IGNORE_URLS', [])
        if ignore_urls:
            rows.append(("TRANSACTIONS_IGNORE_URLS", ", ".join(ignore_urls)))
        else:
            rows.append(("TRANSACTIONS_IGNORE_URLS", "None (all URLs traced)"))
        rows.append((
            "SPAN_STACK_TRACE_MIN_DURATION",
            elastic_apm.get('SPAN_STACK_TRACE_MIN_DURATION', 'N/A'),
        ))
        for key, value in rows:
            out("  {}: {}".format(key, value))
        out("")

        # Check if APM is enabled
        if not apm_active:
            out(warning("APM is not active (APM_ACTIVE=False)"))
            return

        # Verify SERVER_URL is set
        server_url = elastic_apm.get('SERVER_URL')
        if not server_url:
            out(error("ERROR: SERVER_URL is not configured"))
            return

        # Test connection to APM server
        base_url = server_url.rstrip('/')
        headers = {}

        # Add auth token if configured
        if secret_token:
            headers['Authorization'] = 'Bearer {}'.format(secret_token)

        # Step 1: Check if server is reachable (GET /)
        label = "Server reachability: "
        try:
            response = requests.get(
                base_url + '/', headers=headers, timeout=10
            )
            if response.status_code == 200:
                out(label + success("OK"))
                try:
                    server_version = response.json().get('version')
                    if server_version:
                        out("  APM Server version: {}".format(server_version))
                except Exception:
                    pass
            else:
                out(label + error("FAILED (status {})".format(
                    response.status_code
                )))
                return
        except requests.exceptions.ConnectionError as e:
            out(label + error("FAILED"))
            out(error("  Cannot connect: {}".format(str(e))))
            return
        except requests.exceptions.Timeout:
            out(label + error("FAILED (timeout)"))
            return
        except Exception as e:
            out(label + error("FAILED ({})".format(str(e))))
            return

        # Step 2: Check authentication via intake endpoint
        label = "Authentication: "
        try:
            # Send empty NDJSON to intake endpoint to test auth
            intake_url = base_url + '/intake/v2/events'
            intake_headers = headers.copy()
            intake_headers['Content-Type'] = 'application/x-ndjson'

            response = requests.post(
                intake_url, headers=intake_headers, data='', timeout=10
            )

            # 202 = accepted, 400 = bad request (but auth ok)
            if response.status_code in (202, 400):
                out(label + success("OK"))
            elif response.status_code == 401:
                out(label + error("FAILED"))
                out(error("  Authentication failed - check SECRET_TOKEN"))
            elif response.status_code == 403:
                out(label + error("FAILED"))
                out(error("  Access forbidden (403)"))
            else:
                out(label + warning("UNKNOWN (status {})".format(
                    response.status_code
                )))
                out("  Response: {}".format(response.text[:200]))

        except Exception as e:
            out(label + error("FAILED ({})".format(str(e))))
