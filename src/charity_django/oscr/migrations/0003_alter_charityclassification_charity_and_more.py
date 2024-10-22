# Generated by Django 5.0.4 on 2024-10-22 18:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("oscr", "0002_alter_charity_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="charityclassification",
            name="charity",
            field=models.ForeignKey(
                db_constraint=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="classifications",
                to="oscr.charity",
                verbose_name="Charity",
            ),
        ),
        migrations.AlterField(
            model_name="charityfinancialyear",
            name="charity",
            field=models.ForeignKey(
                db_constraint=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="financial_years",
                to="oscr.charity",
                verbose_name="Charity",
            ),
        ),
    ]