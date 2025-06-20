import datetime
from unittest.util import safe_repr
from xml.etree import ElementTree as ET

from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from charity_django.utils.models import CommandLog


class TestCommandLog(TestCase):
    def test_success(self):
        command_name = "test_command_success"
        call_command("logcommand", command_name)
        latest_log = CommandLog.objects.filter(command=command_name).latest("started")

        self.assertEqual(latest_log.command, command_name)
        self.assertEqual(latest_log.status, CommandLog.CommandLogStatus.COMPLETED)
        self.assertIsNotNone(latest_log.completed)
        self.assertFalse("Success stdout" in latest_log.log)
        self.assertFalse("Success print" in latest_log.log)
        self.assertTrue("Success log info" in latest_log.log)
        self.assertTrue("Success log debug" not in latest_log.log)

    def test_warning(self):
        command_name = "test_command_warning"
        call_command("logcommand", command_name)
        latest_log = CommandLog.objects.filter(command=command_name).latest("started")

        self.assertEqual(latest_log.command, command_name)
        self.assertEqual(latest_log.status, CommandLog.CommandLogStatus.COMPLETED)
        self.assertIsNotNone(latest_log.completed)
        self.assertFalse("Success stdout" in latest_log.log)
        self.assertFalse("Success print" in latest_log.log)
        self.assertTrue("Success log info" in latest_log.log)
        self.assertTrue("Success log debug" not in latest_log.log)
        self.assertTrue("Success log warning" in latest_log.log)

    def test_error(self):
        command_name = "test_command_error"
        call_command("logcommand", command_name)
        latest_log = CommandLog.objects.filter(command=command_name).latest("started")

        self.assertEqual(latest_log.command, command_name)
        self.assertEqual(latest_log.status, CommandLog.CommandLogStatus.FAILED)
        self.assertIsNotNone(latest_log.completed)
        self.assertFalse("Success stdout" in latest_log.log)
        self.assertFalse("Success print" in latest_log.log)
        self.assertTrue("Success log info" in latest_log.log)
        self.assertTrue("Success log debug" not in latest_log.log)
        self.assertTrue("Success log warning" in latest_log.log)
        self.assertTrue("Success log error" in latest_log.log)

    def test_error_notify(self):
        with self.settings(ADMINS=[("admin", "admin@example.com")]):
            command_name = "test_command_error"
            call_command("logcommand", command_name)
            call_command("logcommand", "_notify")

            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "[Django] Failed commands")
            self.assertTrue(command_name in mail.outbox[0].body)

    def test_error_notify_twice(self):
        with self.settings(ADMINS=[("admin", "admin@example.com")]):
            command_name = "test_command_error"
            call_command("logcommand", command_name)
            call_command("logcommand", "_notify")
            mail.outbox = []
            call_command("logcommand", "_notify")

            self.assertEqual(len(mail.outbox), 0)

    def test_clean(self):
        CommandLog.objects.create(
            command="test_command_pending",
            status=CommandLog.CommandLogStatus.PENDING,
        )
        CommandLog.objects.create(
            command="test_command_running",
            status=CommandLog.CommandLogStatus.RUNNING,
        )
        CommandLog.objects.create(
            command="test_command_success",
            status=CommandLog.CommandLogStatus.COMPLETED,
        )
        CommandLog.objects.create(
            command="test_command_failed",
            status=CommandLog.CommandLogStatus.FAILED,
        )
        H48_AGO = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            days=2
        )
        CommandLog.objects.update(updated=H48_AGO, started=H48_AGO)
        self.assertEqual(
            CommandLog.objects.filter(
                status=CommandLog.CommandLogStatus.FAILED
            ).count(),
            1,
        )
        self.assertEqual(
            CommandLog.objects.count(),
            4,
        )
        call_command("logcommand", "_clean")
        self.assertEqual(
            CommandLog.objects.filter(
                status=CommandLog.CommandLogStatus.FAILED
            ).count(),
            3,
        )
        self.assertEqual(
            CommandLog.objects.count(),
            4,
        )

    def test_clean_none(self):
        CommandLog.objects.create(
            command="test_command_pending",
            status=CommandLog.CommandLogStatus.PENDING,
        )
        CommandLog.objects.create(
            command="test_command_running",
            status=CommandLog.CommandLogStatus.RUNNING,
        )
        CommandLog.objects.create(
            command="test_command_success",
            status=CommandLog.CommandLogStatus.COMPLETED,
        )
        CommandLog.objects.create(
            command="test_command_failed",
            status=CommandLog.CommandLogStatus.FAILED,
        )
        H2_AGO = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            hours=2
        )
        CommandLog.objects.update(updated=H2_AGO, started=H2_AGO)
        self.assertEqual(
            CommandLog.objects.filter(
                status=CommandLog.CommandLogStatus.FAILED
            ).count(),
            1,
        )
        self.assertEqual(
            CommandLog.objects.count(),
            4,
        )
        call_command("logcommand", "_clean")
        self.assertEqual(
            CommandLog.objects.filter(
                status=CommandLog.CommandLogStatus.FAILED
            ).count(),
            1,
        )
        self.assertEqual(
            CommandLog.objects.count(),
            4,
        )

    def test_exception(self):
        command_name = "test_command_exception"
        error_raised = False
        try:
            call_command("logcommand", command_name)
        except Exception:
            error_raised = True

        self.assertTrue(error_raised)

        latest_log = CommandLog.objects.filter(command=command_name).latest("started")

        self.assertEqual(latest_log.command, command_name)
        self.assertEqual(latest_log.status, CommandLog.CommandLogStatus.FAILED)
        self.assertIsNotNone(latest_log.completed)
        self.assertFalse("Success stdout" in latest_log.log)
        self.assertFalse("Success print" in latest_log.log)
        # self.assertTrue("Success log info" in latest_log.log)
        # self.assertTrue("Success log debug" not in latest_log.log)
        # self.assertTrue("Success log warning" in latest_log.log)
        # self.assertTrue("Success log error" in latest_log.log)
        self.assertTrue("Error message" in latest_log.log)
        self.assertTrue("LogCommandError" in latest_log.log)

    def test_arguments(self):
        command_name = "test_command_arguments"

        args = [
            ("--arg1 1 --arg2 2", ("arg1: 1", "arg2: 2")),
            ("--arg1 1", ("arg1: 1", "arg2: None")),
            ("", ("arg1: None", "arg2: None")),
            ('--arg1 1 --arg2 "quoted string"', ("arg1: 1", "arg2: quoted string")),
        ]
        for argstr, expected_logs in args:
            with self.subTest(argstr=argstr):
                call_command("logcommand", f"{command_name} {argstr}")

                latest_log = CommandLog.objects.filter(
                    command=command_name, cmd_options=argstr
                ).latest("started")

                self.assertEqual(latest_log.command, command_name)
                self.assertEqual(
                    latest_log.status, CommandLog.CommandLogStatus.COMPLETED
                )
                self.assertIsNotNone(latest_log.completed)
                self.assertFalse("Success stdout" in latest_log.log)
                self.assertFalse("Success print" in latest_log.log)
                self.assertTrue("Success log info" in latest_log.log)
                self.assertTrue("Success log debug" not in latest_log.log)

                for expected_log in expected_logs:
                    self.assertTrue(expected_log in latest_log.log)

    def test_arguments_exception(self):
        command_name = "test_command_arguments"
        argstr = "--arg1 99"
        expected_logs = ("arg1: 99", "arg2: None")
        error_raised = False
        try:
            call_command("logcommand", f"{command_name} {argstr}")
        except Exception:
            error_raised = True

        self.assertTrue(error_raised)

        latest_log = CommandLog.objects.filter(
            command=command_name, cmd_options=argstr
        ).latest("started")

        self.assertEqual(latest_log.command, command_name)
        self.assertEqual(latest_log.status, CommandLog.CommandLogStatus.FAILED)
        self.assertIsNotNone(latest_log.completed)
        self.assertFalse("Success stdout" in latest_log.log)
        self.assertFalse("Success print" in latest_log.log)
        # self.assertTrue("Success log info" in latest_log.log)
        # self.assertTrue("Success log debug" not in latest_log.log)
        # self.assertTrue("Success log warning" in latest_log.log)
        # self.assertTrue("Success log error" in latest_log.log)
        self.assertTrue("arg1 is 99" in latest_log.log)
        self.assertTrue("LogCommandError" in latest_log.log)

        for expected_log in expected_logs:
            self.assertTrue(expected_log in latest_log.log)

    def test_tqdm(self):
        command_name = "test_command_tqdm"
        call_command("logcommand", command_name)
        latest_log = CommandLog.objects.filter(command=command_name).latest("started")

        self.assertEqual(latest_log.command, command_name)
        self.assertEqual(latest_log.status, CommandLog.CommandLogStatus.COMPLETED)
        self.assertIsNotNone(latest_log.completed)
        self.assertFalse("Success stdout" in latest_log.log)
        self.assertFalse("Success print" in latest_log.log)
        self.assertFalse("it/s" in latest_log.log)
        self.assertTrue("Success log info" in latest_log.log)
        self.assertTrue("Success log debug" not in latest_log.log)


class TestCommandLogFeeds(TestCase):
    def assertStartsWith(self, a, b, msg=None):
        """Just like self.assertTrue(a > b), but with a nicer default message."""
        if not a.startswith(b):
            standardMsg = "%s does not start with %s" % (safe_repr(a), safe_repr(b))
            self.fail(self._formatMessage(msg, standardMsg))

    def setUp(self):
        # create some command logs for testing
        CommandLog.objects.create(
            command="test_command_2",
            status=CommandLog.CommandLogStatus.FAILED,
            log="Test command 2 failed.",
        )
        c = CommandLog.objects.create(
            command="test_command_running",
            status=CommandLog.CommandLogStatus.RUNNING,
        )
        # create a command log with a long running time
        c = CommandLog.objects.create(
            command="test_command_long_running",
            status=CommandLog.CommandLogStatus.RUNNING,
        )
        c.started = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            days=2
        )
        c.save()
        # create a command log with a pending status
        CommandLog.objects.create(
            command="test_command_pending",
            status=CommandLog.CommandLogStatus.PENDING,
        )
        # create a command log with a long running time and pending
        c = CommandLog.objects.create(
            command="test_command_long_running_pending",
            status=CommandLog.CommandLogStatus.PENDING,
        )
        c.started = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            days=2
        )
        c.save()
        CommandLog.objects.create(
            command="test_command_1",
            status=CommandLog.CommandLogStatus.COMPLETED,
            log="Test command 1 completed successfully.",
        )

    def test_rss_all_commands_feed(self):
        from charity_django.utils.commandlogs.views import RssAllCommandsFeed

        feed = RssAllCommandsFeed()
        items = feed.items()
        self.assertEqual(len(items), 6)
        self.assertEqual(feed.title, "All commands")
        self.assertEqual(
            feed.description, "A list of all commands logged in the system."
        )

    def test_atom_all_commands_feed(self):
        from charity_django.utils.commandlogs.views import AtomAllCommandsFeed

        feed = AtomAllCommandsFeed()
        items = feed.items()
        self.assertEqual(len(items), 6)
        self.assertEqual(feed.title, "All commands")
        self.assertEqual(feed.subtitle, "A list of all commands logged in the system.")

    def test_rss_failed_commands_feed(self):
        from charity_django.utils.commandlogs.views import RssFailedCommandsFeed

        feed = RssFailedCommandsFeed()
        items = feed.items()
        self.assertEqual(len(items), 3)
        self.assertEqual(feed.title, "Failed commands")
        self.assertEqual(
            feed.description, "A list of all failed commands in the system."
        )

    def test_atom_failed_commands_feed(self):
        from charity_django.utils.commandlogs.views import AtomFailedCommandsFeed

        feed = AtomFailedCommandsFeed()
        items = feed.items()
        self.assertEqual(len(items), 3)
        self.assertEqual(feed.title, "Failed commands")
        self.assertEqual(feed.subtitle, "A list of all failed commands in the system.")

    def test_rss_all_commands_feed_url(self):
        response = self.client.get("/command/feed/all.rss")
        self.assertEqual(response.status_code, 200)

        # parse the response content from XML

        root = ET.fromstring(response.content)
        self.assertEqual(root.tag, "rss")
        self.assertEqual(root.find("channel/title").text, "All commands")
        self.assertEqual(
            root.find("channel/link").text, "http://testserver/admin/utils/commandlog/"
        )

        self.assertStartsWith(root.find("channel/item/title").text, "test_command_1")
        self.assertEqual(
            root.find("channel/item/description").text,
            "Test command 1 completed successfully.",
        )
        # check that there are 6 items in the feed
        items = root.findall("channel/item")
        self.assertEqual(len(items), 6)

    def test_rss_failed_commands_feed_url(self):
        response = self.client.get("/command/feed/failed.rss")
        self.assertEqual(response.status_code, 200)

        # parse the response content from XML
        root = ET.fromstring(response.content)
        self.assertEqual(root.tag, "rss")
        self.assertEqual(root.find("channel/title").text, "Failed commands")
        self.assertEqual(
            root.find("channel/link").text, "http://testserver/admin/utils/commandlog/"
        )
        print(root.find("channel/item/title").text)
        self.assertStartsWith(
            root.find("channel/item/title").text, "Failed: test_command_2"
        )
        self.assertEqual(
            root.find("channel/item/description").text,
            "Error log: Test command 2 failed.",
        )
        # check that there are 3 items in the feed
        items = root.findall("channel/item")
        self.assertEqual(len(items), 3)

    def test_atom_all_commands_feed_url(self):
        response = self.client.get("/command/feed/all.atom")
        self.assertEqual(response.status_code, 200)

        # parse the response content from XML
        root = ET.fromstring(response.content)
        self.assertEqual(root.tag, "{http://www.w3.org/2005/Atom}feed")
        self.assertEqual(
            root.find("{http://www.w3.org/2005/Atom}title").text,
            "All commands",
        )
        self.assertEqual(
            root.find("{http://www.w3.org/2005/Atom}link").attrib["href"],
            "http://testserver/admin/utils/commandlog/",
        )

        # check that there are 6 items in the feed
        items = root.findall("{http://www.w3.org/2005/Atom}entry")
        self.assertEqual(len(items), 6)
        self.assertStartsWith(
            items[0].find("{http://www.w3.org/2005/Atom}title").text,
            "test_command_1",
        )
        self.assertEqual(
            items[0].find("{http://www.w3.org/2005/Atom}summary").text,
            "Test command 1 completed successfully.",
        )

    def test_atom_failed_commands_feed_url(self):
        response = self.client.get("/command/feed/failed.atom")
        self.assertEqual(response.status_code, 200)

        # parse the response content from XML
        root = ET.fromstring(response.content)
        self.assertEqual(root.tag, "{http://www.w3.org/2005/Atom}feed")
        self.assertEqual(
            root.find("{http://www.w3.org/2005/Atom}title").text, "Failed commands"
        )
        self.assertEqual(
            root.find("{http://www.w3.org/2005/Atom}link").attrib["href"],
            "http://testserver/admin/utils/commandlog/",
        )

        # check that there are 3 items in the feed
        items = root.findall("{http://www.w3.org/2005/Atom}entry")
        self.assertEqual(len(items), 3)
        self.assertStartsWith(
            items[0].find("{http://www.w3.org/2005/Atom}title").text,
            "Failed: test_command_2",
        )
        self.assertEqual(
            items[0].find("{http://www.w3.org/2005/Atom}summary").text,
            "Error log: Test command 2 failed.",
        )
