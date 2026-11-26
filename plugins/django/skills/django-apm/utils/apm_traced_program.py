import elasticapm
from elasticapm.conf.constants import OUTCOME
from elasticapm.contrib.django.client import get_client


class ApmTracedProgram:
    """Runs a program as an Elastic APM transaction.

    Every call of the instance is one transaction, of type
    `transaction_type` and named `name`. Its result is `success`, or
    `failure` when the program raises an exception: the exception is sent
    to APM and raised again.

    """

    def __init__(self, program, name, transaction_type="importer"):
        self.program = program
        self.name = name
        self.transaction_type = transaction_type

    def __call__(self):
        client = get_client()
        client.begin_transaction(self.transaction_type)
        try:
            result = self.program()
        except Exception:
            client.capture_exception(handled=False)
            elasticapm.set_transaction_outcome(OUTCOME.FAILURE)
            client.end_transaction(self.name, "failure")
            raise
        elasticapm.set_transaction_outcome(OUTCOME.SUCCESS)
        client.end_transaction(self.name, "success")
        return result

    def __repr__(self):
        return "ApmTracedProgram({!r}, {!r})".format(self.program, self.name)
