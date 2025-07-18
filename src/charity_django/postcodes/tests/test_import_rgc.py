import os

import requests_mock
from django.test import TestCase
from requests import Session

from charity_django.postcodes.management.commands._base import (
    GEOPORTAL_API_URL,
    GEOPORTAL_DATA_URL,
)
from charity_django.postcodes.management.commands.import_rgc import Command
from charity_django.postcodes.models import GeoEntity


class TestImportRGC(TestCase):
    def mock_csv_downloads(self, m):
        dirname = os.path.dirname(__file__)
        with open(
            os.path.join(dirname, "data", "api_rgc.json"),
            "rb",
        ) as a:
            m.get(
                f"{GEOPORTAL_API_URL}?q=PRD_RGC&sortBy=-properties.created",
                content=a.read(),
            )
        with open(
            os.path.join(
                dirname, "data", "Register_of_Geographic_Codes_(May_2023)_UK.zip"
            ),
            "rb",
        ) as a:
            m.get(
                GEOPORTAL_DATA_URL.format("da3fb8af12e842a69255b0d21116bcaa"),
                content=a.read(),
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
            assert GeoEntity.objects.count() == 201
            assert GeoEntity.objects.filter(status="Current").count() == 174
            assert GeoEntity.objects.get(code="E13").name == "Inner and Outer London"
