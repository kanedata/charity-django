import csv
import io
from datetime import datetime, timedelta

import psycopg2.extras
import requests_cache
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils.text import slugify

from charity_django.ccni.models import (
    Charity,
    CharityClassification,
    ClassificationTypes,
)


class Command(BaseCommand):
    help = "Import CCNI data from a zip file"
    page_size = 10000

    base_url = "https://www.charitycommissionni.org.uk/umbraco/api/charityApi/ExportSearchResultsToCsv/?include=Linked&include=Removed"

    def logger(self, message, error=False):
        if error:
            self.stderr.write(self.style.ERROR(message))
        self.stdout.write(self.style.SUCCESS(message))

    def handle(self, *args, **options):
        self.session = requests_cache.CachedSession(
            "demo_cache.sqlite",
            expire_after=timedelta(days=1),
        )

        self.charities = []
        self.charity_classification = set()

        self.fetch_file()

    def fetch_file(self):
        self.files = {}
        r = self.session.get(self.base_url)
        r.raise_for_status()

        file = io.StringIO(r.text)
        reader = csv.DictReader(file)
        for k, row in enumerate(reader):
            self.add_charity(row)
        self.save_charities()

    def add_charity(self, record):
        record = {
            slugify(k).replace("-", "_"): v if v != "" else None
            for k, v in record.items()
            if k
        }

        # date fields
        for k, format_ in [
            ("date_registered", "%d/%m/%Y"),
            ("date_for_financial_year_ending", "%d %B %Y"),
        ]:
            record[k] = datetime.strptime(record[k], format_).date()

        # int fields
        for k in [
            "reg_charity_number",
            "sub_charity_number",
            "total_income",
            "total_spending",
            "charitable_spending",
            "income_generation_and_governance",
            "retained_for_future_use",
        ]:
            record[k] = int(record[k])

        # array fields
        for k in [
            "what_the_charity_does",
            "who_the_charity_helps",
            "how_the_charity_works",
        ]:
            record[k] = record.get(k, "").split(",")
            for classification_record in record[k]:
                if classification_record.strip():
                    self.charity_classification.add(
                        (
                            record["reg_charity_number"],
                            ClassificationTypes[k.upper()],
                            classification_record.strip(),
                        )
                    )

        # company number field
        if record.get("company_number") == "0":
            record["company_number"] = None
        if record.get("company_number"):
            record["company_number"] = "NI" + record["company_number"].zfill(6)

        # website field
        if record.get("website") and not record.get("website").startswith("http"):
            record["website"] = "http://" + record["website"]
        self.charities.append(record)

    def _execute_many(self, cursor, statement, values):
        if connection.vendor == "postgresql":
            psycopg2.extras.execute_values(
                cursor,
                statement,
                values,
                page_size=self.page_size,
            )
        else:
            cursor.executemany(
                statement,
                values,
            )

    def save_charities(self):
        with connection.cursor() as cursor, transaction.atomic():
            for object in [Charity, CharityClassification]:
                # delete existing charities
                self.logger(
                    "Deleting existing objects [{}]".format(object._meta.db_table)
                )
                object.objects.all().delete()

                # get field names
                fields = list(f.name for f in object._meta.fields if f.name != "id")

                if object.__name__ == "CharityClassification":
                    values = tuple(self.charity_classification)
                    fields = ["charity_id", "classification_type", "classification"]
                else:
                    values = tuple(
                        tuple(c.get(f) for f in fields) for c in self.charities
                    )

                # validate the first 10 charities
                for c in values[:10]:
                    d = dict(zip(fields, c))
                    o = object(**d)
                    try:
                        o.full_clean()
                    except Exception as e:
                        self.logger("Validation error: {}".format(e), error=True)
                        raise

                # insert new charities
                statement = """INSERT INTO "{table}" ("{fields}") VALUES {placeholder};""".format(
                    table=object._meta.db_table,
                    fields='", "'.join(fields),
                    placeholder="(" + ", ".join(["%s" for f in fields]) + ")"
                    if connection.vendor == "sqlite"
                    else "%s",
                )

                self._execute_many(cursor, statement, values)
                self.logger("Finished table insert [{}]".format(object._meta.db_table))
