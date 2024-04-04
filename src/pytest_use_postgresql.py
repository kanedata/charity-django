import os
import signal

import pytest
from dj_database_url import parse
from django.conf import settings
from testing.postgresql import Postgresql

postgres = os.environ.get("POSTGRESQL_PATH")
initdb = os.environ.get("INITDB_PATH")


# tweak for windows
class PostgresqlWindows(Postgresql):
    terminate_signal = signal.SIGINT

    def terminate(self, *args):
        super(Postgresql, self).terminate()


_POSTGRESQL = PostgresqlWindows(
    postgres=postgres,
    initdb=initdb,
    initdb_args="-U postgres -A trust --encoding=utf8",
)


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(early_config, parser, args):
    os.environ["DJANGO_SETTINGS_MODULE"] = early_config.getini("DJANGO_SETTINGS_MODULE")
    settings.DATABASES["default"] = parse(_POSTGRESQL.url())
    settings.DATABASES["dashboard"] = parse(_POSTGRESQL.url())


def pytest_unconfigure(config):
    _POSTGRESQL.stop()
