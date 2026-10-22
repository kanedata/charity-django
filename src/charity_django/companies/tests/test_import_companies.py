import re
from importlib import resources
from unittest.mock import patch

import requests_mock
from django.test import TestCase
from requests_html import HTMLSession

import charity_django.companies.tests.data
from charity_django.companies.management.commands.import_companies import Command
from charity_django.companies.models import Company


class TestImportCompanies(TestCase):
    def mock_csv_downloads(self, m):
        m.get(
            "http://download.companieshouse.gov.uk/en_output.html",
            text=(
                resources.files(charity_django.companies.tests.data)
                .joinpath("CompaniesHomePage.html")
                .read_text()
            ),
        )
        matcher = re.compile("http://download.companieshouse.gov.uk/BasicCompanyData-")
        m.get(
            matcher,
            content=(
                resources.files(charity_django.companies.tests.data)
                .joinpath("CompaniesHouseTestData.zip")
                .read_bytes()
            ),
        )

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
            command.handle(debug=False, cache=False, sample=0)
            assert Company.objects.count() == 87

    @patch("random.random", side_effect=[0.01, 0.99] * 1_000)
    def test_handle_sample(self, random_mock):
        command = Command()

        with requests_mock.Mocker() as m:
            self.mock_csv_downloads(m)
            # import companies sample is based on a file containing 750_000 companies
            # so to simulate a sample of companies we need to set the sample to 350_000
            command.handle(debug=False, cache=False, sample=350_000)
            assert Company.objects.count() == 44
