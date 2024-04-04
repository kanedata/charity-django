import os
import sys
import unittest.mock

import pytest
import requests
import requests_mock
from django.test import TestCase

from charity_django.ccni.management.commands.import_ccni import Command as CCNICommand
from charity_django.ccni.models import Charity


class MockSession(requests.Session):
    def __init__(self, *args, **kwargs):
        kwargs.pop("expire_after", None)
        super().__init__(*[], **kwargs)


@pytest.fixture(scope="function", autouse=True)
def disable_requests_cache():
    """Replace CachedSession with a regular Session for all test functions"""
    with unittest.mock.patch("requests_cache.CachedSession", MockSession):
        yield


class ImportCCNITestCase(TestCase):
    def _mock_csv_downloads(self, m):
        dirname = os.path.dirname(__file__)
        with open(os.path.join(dirname, "data", "charitydetails_test.csv"), "rb") as a:
            m.get(CCNICommand.base_url, content=a.read())

    def test_charity_import(self):
        command = CCNICommand()
        command.stdout = sys.stdout

        with requests_mock.Mocker() as m:
            self._mock_csv_downloads(m)
            command.handle()
            assert Charity.objects.count() == 365

    def test_charity_import_sample(self):
        command = CCNICommand()
        command.stdout = sys.stdout

        with requests_mock.Mocker() as m:
            self._mock_csv_downloads(m)
            command.handle(sample=10)
            assert Charity.objects.count() == 10

    def test_charity_import_encoding(self):
        command = CCNICommand()
        command.stdout = sys.stdout

        with requests_mock.Mocker() as m:
            self._mock_csv_downloads(m)
            command.handle()
            charity = Charity.objects.get(reg_charity_number=100016)
            assert charity.charity_name == "Fírinne"

    def test_charity_import_twice(self):
        command = CCNICommand()
        command.stdout = sys.stdout

        with requests_mock.Mocker() as m:
            self._mock_csv_downloads(m)
            command.handle()
            command.handle()
            assert Charity.objects.count() == 365
