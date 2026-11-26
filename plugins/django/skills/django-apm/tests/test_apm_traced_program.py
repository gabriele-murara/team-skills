from unittest import mock

from django.test import SimpleTestCase
from elasticapm.conf.constants import OUTCOME

from __TRACED_PROGRAM_MODULE__ import ApmTracedProgram

TRACED_PROGRAM_MODULE = "__TRACED_PROGRAM_MODULE__"


class ApmTracedProgramTestCase(SimpleTestCase):
    def setUp(self):
        patcher = mock.patch("{}.get_client".format(TRACED_PROGRAM_MODULE))
        self.client = patcher.start().return_value
        self.addCleanup(patcher.stop)

        patcher = mock.patch("elasticapm.set_transaction_outcome")
        self.set_outcome = patcher.start()
        self.addCleanup(patcher.stop)

    def test_success_ends_transaction_with_success(self):
        program = mock.Mock(return_value="done")

        result = ApmTracedProgram(program, "scan_folder")()

        self.assertEqual(result, "done")
        self.client.begin_transaction.assert_called_once_with("importer")
        self.client.end_transaction.assert_called_once_with(
            "scan_folder", "success"
        )
        self.set_outcome.assert_called_once_with(OUTCOME.SUCCESS)
        self.client.capture_exception.assert_not_called()

    def test_exception_is_captured_and_raised_again(self):
        program = mock.Mock(side_effect=ValueError("scan failed"))

        with self.assertRaises(ValueError):
            ApmTracedProgram(program, "scan_folder")()

        self.client.capture_exception.assert_called_once_with(handled=False)
        self.client.end_transaction.assert_called_once_with(
            "scan_folder", "failure"
        )
        self.set_outcome.assert_called_once_with(OUTCOME.FAILURE)

    def test_transaction_type_is_used(self):
        program = mock.Mock(return_value=None)

        ApmTracedProgram(program, "process_queue", "worker")()

        self.client.begin_transaction.assert_called_once_with("worker")
