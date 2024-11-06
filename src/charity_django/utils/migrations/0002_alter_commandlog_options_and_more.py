# Generated by Django 5.0.4 on 2024-10-25 10:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="commandlog",
            options={
                "ordering": ("-started",),
                "verbose_name": "Command Log",
                "verbose_name_plural": "Command Logs",
            },
        ),
        migrations.AlterField(
            model_name="commandlog",
            name="cmd_options",
            field=models.TextField(
                blank=True, null=True, verbose_name="Command options"
            ),
        ),
    ]