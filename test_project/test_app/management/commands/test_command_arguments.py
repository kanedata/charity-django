import logging

from django.core.management.base import BaseCommand

from .test_command_exception import LogCommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Test command which prints a message and completes successfully with arguments"
    )

    def add_arguments(self, parser):
        parser.add_argument("--arg1", type=int, help="First argument")
        parser.add_argument("--arg2", type=str, help="Second argument")

    def handle(self, *args, **options):
        self.stdout.write("Success stdout")
        print("Success print")
        logger.info("Success log info")
        logger.debug("Success log debug")

        arg1 = options["arg1"]
        arg2 = options["arg2"]
        print(f"arg1: {arg1}")
        print(f"arg2: {arg2}")

        if arg1 == 99:
            raise LogCommandError("arg1 is 99")
