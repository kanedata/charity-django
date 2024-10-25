from django.apps import AppConfig
from django.conf import settings


class TestAppConfig(AppConfig):
    name = (
        "test_project.test_app"
        if "test_project.test_app" in settings.INSTALLED_APPS
        else "test_app"
    )
    verbose_name = "Test App"
