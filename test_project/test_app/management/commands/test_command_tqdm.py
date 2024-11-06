import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Test command which prints a message and completes successfully"

    def handle(self, *args, **options):
        self.stdout.write("Success stdout")
        print("Success print")
        logger.info("Success log info")
        logger.debug("Success log debug")

        for i in tqdm(range(100)):
            pass