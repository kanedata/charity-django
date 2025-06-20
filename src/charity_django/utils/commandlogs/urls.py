from django.urls import path

from charity_django.utils.commandlogs.views import (
    AtomAllCommandsFeed,
    AtomFailedCommandsFeed,
    RssAllCommandsFeed,
    RssFailedCommandsFeed,
)

app_name = "charity_django.utils.commandlogs"
urlpatterns = [
    path("all.rss", RssAllCommandsFeed(), name="all-commands-rss"),
    path("failed.rss", RssFailedCommandsFeed(), name="failed-commands-rss"),
    path("all.atom", AtomAllCommandsFeed(), name="all-commands-atom"),
    path("failed.atom", AtomFailedCommandsFeed(), name="failed-commands-atom"),
]
