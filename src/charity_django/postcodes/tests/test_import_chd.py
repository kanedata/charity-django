from importlib import resources

import requests_mock
from django.test import TestCase
from requests import Session

import charity_django.postcodes.tests.data
from charity_django.postcodes.management.commands._base import (
    GEOPORTAL_API_URL,
    GEOPORTAL_DATA_URL,
)
from charity_django.postcodes.management.commands.import_chd import Command
from charity_django.postcodes.models import GeoCode


class TestImportCHD(TestCase):
    def mock_csv_downloads(self, m):
        m.get(
            f"{GEOPORTAL_API_URL}?q=PRD_CHD&sortBy=-properties.created",
            content=(
                resources.files(charity_django.postcodes.tests.data)
                .joinpath("api_chd.json")
                .read_bytes()
            ),
        )
        m.get(
            GEOPORTAL_DATA_URL.format("14881034435e45a18cb5531513202400"),
            content=(
                resources.files(charity_django.postcodes.tests.data)
                .joinpath("Code_History_Database_May_2023_UK.zip")
                .read_bytes()
            ),
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
            assert GeoCode.objects.count() == 500
            assert GeoCode.objects.filter(STATUS="live").count() == 417
            assert (
                GeoCode.objects.get(GEOGCD="E04005721").GEOGNM
                == "Skidbrooke with Saltfleet Haven"
            )
            assert GeoCode.objects.get(GEOGCD="E33003018").GEOGNM is None
