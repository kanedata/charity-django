from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.feedgenerator import Atom1Feed

from charity_django.utils.models import CommandLog


class RssAllCommandsFeed(Feed):
    title = "All commands"
    author_name = "Admin"
    description = "A list of all commands logged in the system."

    def link(self):
        self.content_type = ContentType.objects.get_for_model(CommandLog)
        return reverse(
            "admin:{}_{}_changelist".format(
                self.content_type.app_label, self.content_type.model
            )
        )

    def items(self):
        return CommandLog.objects.order_by("-started")[:20]

    def item_title(self, item):
        return str(item)

    def item_description(self, item):
        return item.log

    def item_pubdate(self, item):
        return item.updated

    def item_updateddate(self, item):
        return item.updated

    def item_link(self, item):
        return reverse(
            "admin:{}_{}_change".format(
                self.content_type.app_label, self.content_type.model
            ),
            args=[item.pk],
        )


class AtomAllCommandsFeed(RssAllCommandsFeed):
    feed_type = Atom1Feed
    subtitle = RssAllCommandsFeed.description


class RssFailedCommandsFeed(RssAllCommandsFeed):
    title = "Failed commands"
    description = "A list of all failed commands in the system."

    def items(self):
        # either failed commands or commands that have been running for more than a day
        started = timezone.now() - timedelta(days=1)
        return CommandLog.objects.filter(
            Q(status=CommandLog.CommandLogStatus.FAILED)
            | Q(
                status__in=[
                    CommandLog.CommandLogStatus.PENDING,
                    CommandLog.CommandLogStatus.RUNNING,
                ],
                started__lt=started,
            )
        ).order_by("-started")[:20]

    def item_title(self, item):
        return f"Failed: {str(item)}"

    def item_description(self, item):
        return f"Error log: {item.log if item.log else 'No log available'}"


class AtomFailedCommandsFeed(RssFailedCommandsFeed):
    feed_type = Atom1Feed
    subtitle = RssFailedCommandsFeed.description
