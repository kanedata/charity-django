import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LogCommandError(Exception):
    pass


class Command(BaseCommand):
    help = "Test command which prints a message and then raises an exception"

    def handle(self, *args, **options):
        self.stdout.write("Success stdout")
        print("Success print")
        logger.info("Success log")
        logger.debug("Success log debug")
        logger.warning("Success log warning")
        logger.error("Success log error")

        raise LogCommandError("Error message")
