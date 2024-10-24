from charity_django.utils.models import CommandLog
from django.core.management import call_command
from django.test import TestCase


class TestCommandLog(TestCase):
    def test_success(self):
        command_name = "test_command_success"
        call_command("logcommand", command_name)
        latest_log = CommandLog.objects.filter(command=command_name).latest("started")

        self.assertEqual(latest_log.command, command_name)
        self.assertEqual(latest_log.status, CommandLog.CommandLogStatus.COMPLETED)
        self.assertIsNotNone(latest_log.completed)
        self.assertTrue("Success stdout" in latest_log.log)
        self.assertTrue("Success print" in latest_log.log)
        self.assertTrue("Success log info" in latest_log.log)
        self.assertTrue("Success log debug" not in latest_log.log)

    def test_warning(self):
        command_name = "test_command_warning"
        call_command("logcommand", command_name)
        latest_log = CommandLog.objects.filter(command=command_name).latest("started")

        self.assertEqual(latest_log.command, command_name)
        self.assertEqual(latest_log.status, CommandLog.CommandLogStatus.COMPLETED)
        self.assertIsNotNone(latest_log.completed)
        self.assertTrue("Success stdout" in latest_log.log)
        self.assertTrue("Success print" in latest_log.log)
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
        self.assertTrue("Success stdout" in latest_log.log)
        self.assertTrue("Success print" in latest_log.log)
        self.assertTrue("Success log info" in latest_log.log)
        self.assertTrue("Success log debug" not in latest_log.log)
        self.assertTrue("Success log warning" in latest_log.log)
        self.assertTrue("Success log error" in latest_log.log)

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
        self.assertTrue("Success stdout" in latest_log.log)
        self.assertTrue("Success print" in latest_log.log)
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
                self.assertTrue("Success stdout" in latest_log.log)
                self.assertTrue("Success print" in latest_log.log)
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
        self.assertTrue("Success stdout" in latest_log.log)
        self.assertTrue("Success print" in latest_log.log)
        # self.assertTrue("Success log info" in latest_log.log)
        # self.assertTrue("Success log debug" not in latest_log.log)
        # self.assertTrue("Success log warning" in latest_log.log)
        # self.assertTrue("Success log error" in latest_log.log)
        self.assertTrue("arg1 is 99" in latest_log.log)
        self.assertTrue("LogCommandError" in latest_log.log)

        for expected_log in expected_logs:
            self.assertTrue(expected_log in latest_log.log)
