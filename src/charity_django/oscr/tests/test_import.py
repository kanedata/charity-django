import sys
import unittest.mock
from importlib import resources

import pytest
import requests
import requests_mock
from django.test import TestCase

import charity_django.oscr.tests.data
from charity_django.oscr.management.commands.import_oscr import Command as OSCRCommand
from charity_django.oscr.models import Charity


class MockSession(requests.Session):
    def __init__(self, *args, **kwargs):
        kwargs.pop("expire_after", None)
        super().__init__(*[], **kwargs)


@pytest.fixture(scope="function", autouse=True)
def disable_requests_cache():
    """Replace CachedSession with a regular Session for all test functions"""
    with unittest.mock.patch("requests_cache.CachedSession", MockSession):
        yield


class ImportOSCRTestCase(TestCase):
    def _mock_csv_downloads(self, m):
        m.get(
            OSCRCommand.base_urls[0],
            content=(
                resources.files(charity_django.oscr.tests.data)
                .joinpath("CharityExport-Test.zip")
                .read_bytes()
            ),
        )
        m.get(
            OSCRCommand.base_urls[1],
            content=(
                resources.files(charity_django.oscr.tests.data)
                .joinpath("CharityExport-5Years-Test.zip")
                .read_bytes()
            ),
        )
        m.get(
            OSCRCommand.base_urls[2],
            content=(
                resources.files(charity_django.oscr.tests.data)
                .joinpath("CharityExport-Removed-Test.zip")
                .read_bytes()
            ),
        )

    def test_charity_import(self):
        command = OSCRCommand()
        command.stdout = sys.stdout

        with requests_mock.Mocker() as m:
            self._mock_csv_downloads(m)
            command.handle()
            assert Charity.objects.count() == 59

    def test_charity_import_sample(self):
        command = OSCRCommand()
        command.stdout = sys.stdout

        with requests_mock.Mocker() as m:
            self._mock_csv_downloads(m)
            command.handle(sample=10)
            assert Charity.objects.count() == 10

    def test_charity_import_twice(self):
        command = OSCRCommand()
        command.stdout = sys.stdout

        with requests_mock.Mocker() as m:
            self._mock_csv_downloads(m)
            command.handle()
            command.handle()
            assert Charity.objects.count() == 59
