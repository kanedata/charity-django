import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test command which prints a message and completes successfully"

    def handle(self, *args, **options):
        self.stdout.write("Success stdout")
        print("Success print")
        logger.info("Success log info")
        logger.debug("Success log debug")
        logger.warning("Success log warning")
