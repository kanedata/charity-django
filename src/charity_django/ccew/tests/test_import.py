import os
import sys
import unittest.mock

import pytest
import requests
import requests_mock
from django.test import TestCase

from charity_django.ccew.management.commands.import_ccew import Command as CCEWCommand
from charity_django.ccew.models import Charity


class MockSession(requests.Session):
    def __init__(self, *args, **kwargs):
        kwargs.pop("expire_after", None)
        super().__init__(*[], **kwargs)


@pytest.fixture(scope="function", autouse=True)
def disable_requests_cache():
    """Replace CachedSession with a regular Session for all test functions"""
    with unittest.mock.patch("requests_cache.CachedSession", MockSession):
        yield


class ImportTestCase(TestCase):
    def _mock_csv_downloads(self, m):
        dirname = os.path.dirname(__file__)
        files = CCEWCommand.ccew_file_to_object
        for file in files:
            with open(
                os.path.join(dirname, "data", f"publicextract.{file}.zip"), "rb"
            ) as a:
                m.get(CCEWCommand.base_url.format(file), content=a.read())

    def test_charity_import(self):
        command = CCEWCommand()
        command.stdout = sys.stdout

        with requests_mock.Mocker() as m:
            self._mock_csv_downloads(m)
            command.handle()
            assert Charity.objects.filter(linked_charity_number=0).count() == 200

    def test_charity_import_encoding(self):
        command = CCEWCommand()
        command.stdout = sys.stdout

        with requests_mock.Mocker() as m:
            self._mock_csv_downloads(m)
            command.handle()
            assert (
                Charity.objects.get(organisation_number=281345).charity_name
                == "Howard’s land Religion Charitable Incorporated Organisation"
            )

    def test_charity_import_twice(self):
        command = CCEWCommand()
        command.stdout = sys.stdout

        with requests_mock.Mocker() as m:
            self._mock_csv_downloads(m)
            command.handle()
            command.handle()
            assert Charity.objects.filter(linked_charity_number=0).count() == 200
