import os
import re

import requests_mock
from django.test import TestCase
from requests import Response
from requests_html import HTMLSession

from charity_django.companies.management.commands.import_companies import Command
from charity_django.companies.models import Company


class TestImportCompanies(TestCase):
    def mock_csv_downloads(self, m):
        dirname = os.path.dirname(__file__)
        with open(os.path.join(dirname, "data", "CompaniesHomePage.html")) as a:
            m.get("http://download.companieshouse.gov.uk/en_output.html", text=a.read())
        with open(
            os.path.join(dirname, "data", "CompaniesHouseTestData.zip"), "rb"
        ) as a:
            matcher = re.compile(
                "http://download.companieshouse.gov.uk/BasicCompanyData-"
            )
            m.get(matcher, content=a.read())

    def test_set_session(self):
        command = Command()

        assert hasattr(command, "session") is False
        command.set_session()
        assert hasattr(command, "session") is True
        assert isinstance(command.session, HTMLSession)

    def test_fetch_file(self):
        command = Command()

        with requests_mock.Mocker() as m:
            self.mock_csv_downloads(m)
            command.set_session()
            command.fetch_file()
            assert Company.objects.count() == 87

    def test_handle(self):
        command = Command()

        with requests_mock.Mocker() as m:
            self.mock_csv_downloads(m)
            command.handle(debug=False, cache=False)
            assert Company.objects.count() == 87
