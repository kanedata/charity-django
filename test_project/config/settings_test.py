from test_project.config.settings import *  # noqa: F401, F403
from test_project.config.settings import INSTALLED_APPS

replace_apps = {
    "test_app": "test_project.test_app",
}

INSTALLED_APPS = [replace_apps.get(app, app) for app in INSTALLED_APPS]
