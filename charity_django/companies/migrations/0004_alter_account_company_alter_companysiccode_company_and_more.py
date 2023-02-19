# Generated by Django 4.1.5 on 2023-02-18 19:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0003_remove_company_uri_alter_account_category_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="account",
            name="company",
            field=models.ForeignKey(
                db_column="CompanyNumber",
                db_constraint=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="accounts",
                to="companies.company",
            ),
        ),
        migrations.AlterField(
            model_name="companysiccode",
            name="company",
            field=models.ForeignKey(
                db_column="CompanyNumber",
                db_constraint=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sic_codes",
                to="companies.company",
            ),
        ),
        migrations.AlterField(
            model_name="companysiccode",
            name="sic_code",
            field=models.ForeignKey(
                db_column="code",
                db_constraint=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="companies",
                to="companies.siccode",
            ),
        ),
        migrations.AlterField(
            model_name="previousname",
            name="company",
            field=models.ForeignKey(
                db_column="CompanyNumber",
                db_constraint=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="previous_names",
                to="companies.company",
            ),
        ),
    ]