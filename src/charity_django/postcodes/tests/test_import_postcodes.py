from importlib import resources

import requests_mock
from django.test import TestCase
from requests import Session

import charity_django.postcodes.tests.data
from charity_django.postcodes.management.commands._base import (
    GEOPORTAL_API_URL,
    GEOPORTAL_DATA_URL,
)
from charity_django.postcodes.management.commands.import_postcodes import Command
from charity_django.postcodes.models import GeoCode, Postcode


class TestImportPostcodes(TestCase):
    def mock_csv_downloads(self, m):
        m.get(
            f"{GEOPORTAL_API_URL}?q=PRD_NSPL&sortBy=-properties.created",
            content=(
                resources.files(charity_django.postcodes.tests.data)
                .joinpath("api_nspl.json")
                .read_bytes()
            ),
        )
        m.get(
            GEOPORTAL_DATA_URL.format("077631e063eb4e1ab43575d01381ec33"),
            content=(
                resources.files(charity_django.postcodes.tests.data)
                .joinpath("NSPL_MAY_2026_TEST.zip")
                .read_bytes()
            ),
        )

    def setUp(self):
        GeoCode.objects.create(
            GEOGCD="E06000065",
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
            assert Postcode.objects.count() == 2_000
            assert (
                Postcode.objects.filter(local_authority_id="E06000065").count() == 200
            )
            assert Postcode.objects.filter(USERTYPE=1).count() == 494
            assert Postcode.objects.filter(IMD=13716).count() == 26
