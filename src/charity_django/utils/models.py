from django.db import models


class CommandLog(models.Model):
    class CommandLogStatus(models.IntegerChoices):
        PENDING = 0
        RUNNING = 1
        COMPLETED = 2
        FAILED = 3

    command = models.CharField(max_length=255)
    cmd_options = models.TextField(
        null=True, blank=True, verbose_name="Command options"
    )
    started = models.DateTimeField(
        auto_now_add=True, verbose_name="When the command started"
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name="When the command was last updated",
    )
    completed = models.DateTimeField(
        null=True, blank=True, verbose_name="When the command completed"
    )
    notified = models.DateTimeField(
        null=True, blank=True, verbose_name="When a notification was sent to admins"
    )
    status = models.IntegerField(
        choices=CommandLogStatus.choices, default=CommandLogStatus.PENDING
    )
    log = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{} {} ({:%Y-%m-%d %H:%M:%S})".format(
            self.command, self.cmd_options if self.cmd_options else "", self.started
        )

    class Meta:
        verbose_name = "Command Log"
        verbose_name_plural = "Command Logs"
        ordering = ("-started",)
