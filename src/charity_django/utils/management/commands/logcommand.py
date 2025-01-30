import datetime
import logging
import shlex

from django.core.mail import mail_admins
from django.core.management import call_command
from django.core.management.base import BaseCommand

from charity_django.utils.models import CommandLog


class CommandLogHandler(logging.StreamHandler):
    def __init__(self, commandlog):
        logging.StreamHandler.__init__(self)
        self.commandlog = commandlog
        self.log = ""
        self.errors = 0

    def emit(self, record):
        msg = self.format(record)
        if not self.commandlog.log:
            self.commandlog.log = ""
        self.commandlog.log += msg + self.terminator
        self.log += msg + self.terminator
        if record.levelno in (logging.ERROR, logging.CRITICAL):
            self.errors += 1
        self.commandlog.updated = datetime.datetime.now(datetime.timezone.utc)
        self.commandlog.save()
        self.flush()

    def teardown(self):
        if self.errors > 0:
            self.commandlog.status = CommandLog.CommandLogStatus.FAILED
        else:
            self.commandlog.status = CommandLog.CommandLogStatus.COMPLETED
        if self.log and not self.commandlog.log:
            self.commandlog.logs = self.log
        self.commandlog.updated = datetime.datetime.now(datetime.timezone.utc)
        self.commandlog.completed = datetime.datetime.now(datetime.timezone.utc)
        self.commandlog.save()


class Command(BaseCommand):
    help = "Wrap a django command to save log messages"

    def add_arguments(self, parser):
        parser.add_argument("command", nargs="+")

    def handle(self, *args, **options):
        # handle a couple of special cases
        # 1. If given "_clean" it will mark any jobs that are still marked as pending but last updated over 24 hours ago as failed
        # 2. If given "_notify" it will send an update of any failed jobs to admins
        if options["command"][0] == "_clean":
            H24_AGO = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
                days=1
            )
            CommandLog.objects.filter(
                status__in=[
                    CommandLog.CommandLogStatus.RUNNING,
                    CommandLog.CommandLogStatus.PENDING,
                ],
                updated__lte=H24_AGO,
            ).update(status=CommandLog.CommandLogStatus.FAILED)
            return
        elif options["command"][0] == "_notify":
            not_notified = CommandLog.objects.filter(
                status=CommandLog.CommandLogStatus.FAILED, notified__isnull=True
            )
            if not_notified.count() == 0:
                return
            messages = []
            for log in not_notified:
                messages.append(
                    f"- {log.command} {log.cmd_options} ({log.started:%Y-%m-%d %H:%M:%S})"
                )
                log.notified = datetime.datetime.now(datetime.timezone.utc)
                log.save()
            message = "The following commands have failed:\n\n" + "\n".join(messages)
            mail_admins("Failed commands", message, fail_silently=False)
            return

        parsed_options = " ".join(options["command"]).split(" ", 1)
        if len(parsed_options) == 1:
            command, cmd_options = parsed_options[0], None
        else:
            command, cmd_options = parsed_options
        self.stdout.write(f"Running command: {command}")
        self.stdout.write(f"With options: {cmd_options}")

        command_log = CommandLog.objects.create(
            command=command,
            cmd_options=cmd_options,
            status=CommandLog.CommandLogStatus.RUNNING,
            started=datetime.datetime.now(datetime.timezone.utc),
            updated=datetime.datetime.now(datetime.timezone.utc),
        )

        command_logger = CommandLogHandler(command_log)
        command_log_format = logging.Formatter(
            "{levelname} {asctime} [{name}] {message}", style="{"
        )
        command_logger.setFormatter(command_log_format)
        command_logger.setLevel(logging.INFO)

        logger = logging.getLogger()
        logger.addHandler(command_logger)
        logger.setLevel(logging.INFO)

        try:
            if cmd_options:
                call_command(command, shlex.split(cmd_options))
            else:
                call_command(command)
        except Exception as err:
            logger.exception(err)
            command_logger.teardown()
            raise

        command_logger.teardown()
