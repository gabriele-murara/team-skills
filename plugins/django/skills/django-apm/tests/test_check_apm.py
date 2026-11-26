from io import StringIO
from unittest import mock

import requests
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

SERVER_URL = "http://apm.example.com:8200"
TOKEN = "secret-token"


def _response(status_code, json_data=None):
    response = mock.Mock(status_code=status_code, text="")
    response.json.return_value = json_data or {}
    return response


class CheckApmTestCase(SimpleTestCase):
    def _call(self):
        out = StringIO()
        call_command("check_apm", stdout=out)
        return out.getvalue()

    @override_settings(APM_ACTIVE=False)
    def test_apm_not_active(self):
        with mock.patch("requests.get") as get:
            output = self._call()

        self.assertIn("APM is not active", output)
        get.assert_not_called()

    @override_settings(APM_ACTIVE=True, ELASTIC_APM={})
    def test_server_url_not_configured(self):
        with mock.patch("requests.get") as get:
            output = self._call()

        self.assertIn("SERVER_URL is not configured", output)
        get.assert_not_called()

    @override_settings(
        APM_ACTIVE=True,
        ELASTIC_APM={"SERVER_URL": SERVER_URL, "SECRET_TOKEN": TOKEN},
    )
    def test_server_reachable_and_authenticated(self):
        with mock.patch("requests.get") as get, \
                mock.patch("requests.post") as post:
            get.return_value = _response(200, {"version": "8.12.0"})
            post.return_value = _response(202)
            output = self._call()

        self.assertIn("secr***", output)
        self.assertNotIn(TOKEN, output)
        self.assertIn("Server reachability: OK", output)
        self.assertIn("APM Server version: 8.12.0", output)
        self.assertIn("Authentication: OK", output)
        headers = post.call_args.kwargs["headers"]
        self.assertEqual(
            headers["Authorization"], "Bearer {}".format(TOKEN)
        )

    @override_settings(
        APM_ACTIVE=True,
        ELASTIC_APM={"SERVER_URL": SERVER_URL, "SECRET_TOKEN": TOKEN},
    )
    def test_authentication_failed(self):
        with mock.patch("requests.get") as get, \
                mock.patch("requests.post") as post:
            get.return_value = _response(200)
            post.return_value = _response(401)
            output = self._call()

        self.assertIn("Authentication failed - check SECRET_TOKEN", output)

    @override_settings(APM_ACTIVE=True, ELASTIC_APM={"SERVER_URL": SERVER_URL})
    def test_server_not_reachable(self):
        with mock.patch("requests.get") as get, \
                mock.patch("requests.post") as post:
            get.side_effect = requests.exceptions.ConnectionError("refused")
            output = self._call()

        self.assertIn("Cannot connect", output)
        post.assert_not_called()
