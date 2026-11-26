"""
Management command to check Elastic APM connection.
"""
import requests
from django.conf import settings
from django_rich.management import RichCommand
from rich.markup import escape
from rich.table import Table

# One entry for every flag of the processes without HTTP that are traced
# (APM_<PROCESS>_ACTIVE). Empty list if no process is traced.
PROCESS_FLAGS = ['APM_IMPORTER_ACTIVE']


class Command(RichCommand):
    """
    Verifies Elastic APM configuration and connection.
    """

    help = 'Check Elastic APM connection and display configuration'

    def handle(self, *args, **options):
        console = self.console

        console.print("\n[bold]Elastic APM Configuration Check[/bold]\n")

        # Get APM configuration
        apm_active = getattr(settings, 'APM_ACTIVE', False)
        elastic_apm = getattr(settings, 'ELASTIC_APM', {})

        # Display configuration table
        table = Table(title="APM Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("APM_ACTIVE", str(apm_active))
        for flag in PROCESS_FLAGS:
            table.add_row(flag, str(getattr(settings, flag, False)))
        for key in ['ENABLED', 'DISABLE_SEND', 'SERVICE_NAME', 'HOSTNAME',
                    'SERVER_URL', 'DEBUG']:
            table.add_row(key, escape(str(elastic_apm.get(key, 'N/A'))))
        secret_token = elastic_apm.get('SECRET_TOKEN')
        if secret_token:
            masked_token = "{}***".format(escape(secret_token[:4]))
        else:
            masked_token = "Not set"
        table.add_row("SECRET_TOKEN", masked_token)

        # Performance tuning settings
        sample_rate = elastic_apm.get('TRANSACTION_SAMPLE_RATE', 'N/A')
        table.add_row("TRANSACTION_SAMPLE_RATE", str(sample_rate))

        ignore_urls = elastic_apm.get('TRANSACTIONS_IGNORE_URLS', [])
        if ignore_urls:
            table.add_row(
                "TRANSACTIONS_IGNORE_URLS", escape(", ".join(ignore_urls))
            )
        else:
            table.add_row(
                "TRANSACTIONS_IGNORE_URLS", "None (all URLs traced)"
            )

        stack_trace_min = elastic_apm.get(
            'SPAN_STACK_TRACE_MIN_DURATION', 'N/A'
        )
        table.add_row("SPAN_STACK_TRACE_MIN_DURATION", str(stack_trace_min))

        console.print(table)
        console.print()

        # Check if APM is enabled
        if not apm_active:
            console.print(
                "[yellow]APM is not active (APM_ACTIVE=False)[/yellow]"
            )
            return

        # Verify SERVER_URL is set
        server_url = elastic_apm.get('SERVER_URL')
        if not server_url:
            console.print("[red]ERROR: SERVER_URL is not configured[/red]")
            return

        # Test connection to APM server
        base_url = server_url.rstrip('/')
        headers = {}

        # Add auth token if configured
        if secret_token:
            headers['Authorization'] = 'Bearer {}'.format(secret_token)

        # Step 1: Check if server is reachable (GET /)
        console.print("Server reachability: ", end="")
        try:
            response = requests.get(
                base_url + '/', headers=headers, timeout=10
            )
            if response.status_code == 200:
                console.print("[green]OK[/green]")
                try:
                    server_version = response.json().get('version')
                    if server_version:
                        console.print(
                            "  APM Server version: {}".format(
                                escape(str(server_version))
                            )
                        )
                except Exception:
                    pass
            else:
                console.print("[red]FAILED (status {})[/red]".format(
                    response.status_code
                ))
                return
        except requests.exceptions.ConnectionError as e:
            console.print("[red]FAILED[/red]")
            console.print(
                "[red]  Cannot connect: {}[/red]".format(escape(str(e)))
            )
            return
        except requests.exceptions.Timeout:
            console.print("[red]FAILED (timeout)[/red]")
            return
        except Exception as e:
            console.print("[red]FAILED ({})[/red]".format(escape(str(e))))
            return

        # Step 2: Check authentication via intake endpoint
        console.print("Authentication: ", end="")
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
                console.print("[green]OK[/green]")
            elif response.status_code == 401:
                console.print("[red]FAILED[/red]")
                console.print(
                    "[red]  Authentication failed - check SECRET_TOKEN[/red]"
                )
            elif response.status_code == 403:
                console.print("[red]FAILED[/red]")
                console.print("[red]  Access forbidden (403)[/red]")
            else:
                console.print("[yellow]UNKNOWN (status {})[/yellow]".format(
                    response.status_code
                ))
                console.print(
                    "  Response: {}".format(escape(response.text[:200]))
                )

        except Exception as e:
            console.print("[red]FAILED ({})[/red]".format(escape(str(e))))
