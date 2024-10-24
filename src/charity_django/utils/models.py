from django.db import models


class CommandLog(models.Model):
    class CommandLogStatus(models.IntegerChoices):
        PENDING = 0
        RUNNING = 1
        COMPLETED = 2
        FAILED = 3

    command = models.CharField(max_length=255)
    cmd_options = models.TextField(null=True, blank=True)
    started = models.DateTimeField(auto_now_add=True)
    completed = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(
        choices=CommandLogStatus.choices, default=CommandLogStatus.PENDING
    )
    log = models.TextField(null=True, blank=True)
