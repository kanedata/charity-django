import os

import requests_mock
from django.test import TestCase
from requests import Session

from charity_django.postcodes.management.commands.import_postcodes import (
    POSTCODES_URL,
    Command,
)
from charity_django.postcodes.models import GeoCode, Postcode


class TestImportPostcodes(TestCase):
    def mock_csv_downloads(self, m):
        dirname = os.path.dirname(__file__)
        with open(os.path.join(dirname, "data", "NSPL_2021_TEST.zip"), "rb") as a:
            m.get(POSTCODES_URL, content=a.read())

    def setUp(self):
        GeoCode.objects.create(
            GEOGCD="E09000033",
        )

    def test_set_session(self):
        command = Command()

        assert hasattr(command, "session") is False
        command.set_session()
        assert hasattr(command, "session") is True
        assert isinstance(command.session, Session)

    def test_handle(self):
        command = Command()

        with requests_mock.Mocker() as m:
            self.mock_csv_downloads(m)
            command.handle(debug=False, cache=False)
            assert Postcode.objects.count() == 1_000
            assert (
                Postcode.objects.filter(local_authority_id="E09000033").count() == 290
            )
            assert Postcode.objects.filter(USERTYPE=1).count() == 399
            assert Postcode.objects.filter(IMD=8940).count() == 1
