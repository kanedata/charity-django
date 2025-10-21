import csv
import io
import logging
import random
import re
import zipfile
from datetime import date, datetime, timedelta

import psycopg2.extras
import requests_cache
from django.core.management.base import BaseCommand
from django.db import connections, router, transaction
from django.db.utils import OperationalError, ProgrammingError
from django.utils.text import slugify

from charity_django.oscr.models import (
    Charity,
    CharityClassification,
    CharityFinancialYear,
    ClassificationTypes,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

fy_fields = list(
    f.get_attname_column()[1]
    for f in CharityFinancialYear._meta.fields
    if f.name != "id"
)
char_fields = list(
    f.get_attname_column()[1] for f in Charity._meta.fields if f.name != "id"
)
classification_fields = list(
    f.get_attname_column()[1]
    for f in CharityClassification._meta.fields
    if f.name != "id"
)
insolvency_regex = re.compile(r"\(?subject to insolvency proceedings\)?", re.IGNORECASE)


class Command(BaseCommand):
    help = "Import OSCR data from a zip file"
    page_size = 10_000

    base_urls = (
        "https://www.oscr.org.uk/download/charity-register",
        "https://www.oscr.org.uk/download/5-years-charity-register",
        "https://www.oscr.org.uk/download/charity-former-register",
    )

    def _get_db(self):
        return router.db_for_write(Charity)

    def _get_connection(self):
        return connections[self._get_db()]

    def logger(self, message, error=False):
        if error:
            logger.error(message)
            return
        logger.info(message)

    def add_arguments(self, parser):
        parser.add_argument("--sample", type=int, default=0)

    def handle(self, *args, **options):
        self.session = requests_cache.CachedSession(
            "demo_cache.sqlite",
            expire_after=timedelta(days=1),
        )
        self.sample = options.get("sample")

        self.charities = {}
        self.financial_years = {}
        self.charity_classification = set()

        self.fetch_file()

    def _execute_many(self, cursor, statement, values):
        connection = self._get_connection()
        try:
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
        except (OperationalError, ProgrammingError) as e:
            self.logger(e, error=True)
            self.logger(statement, error=True)
            self.logger(values[0:10], error=True)
            raise

    def fetch_file(self):
        self.files = {}
        for url in self.base_urls:
            response = self.session.get(url)
            response.raise_for_status()

            try:
                z = zipfile.ZipFile(io.BytesIO(response.content))
            except zipfile.BadZipFile:
                self.logger(response.content[0:1000])
                raise
            for file_ in z.infolist():
                self.logger("Opening: {}".format(file_.filename))
                with z.open(file_) as csvfile:
                    reader = csv.DictReader(io.TextIOWrapper(csvfile, encoding="utf8"))
                    rowcount = 0
                    for row in reader:
                        rowcount += 1
                        self.add_charity(row)
            z.close()
        self.save_charities()

    def add_charity(self, record):
        record = {
            slugify(k.strip().replace("/", "_")).replace("-", "_"): v.strip()
            if v
            not in (
                "",
                "-",
                "-, -",
            )
            else None
            for k, v in record.items()
            if k
        }

        # array fields
        for k in [
            "purposes",
            "beneficiaries",
            "activities",
        ]:
            if record.get(k):
                reader = csv.reader([record[k]], delimiter=",", quotechar="'")
                record[k] = list(next(reader))
                for classification_record in record[k]:
                    if classification_record.strip():
                        self.charity_classification.add(
                            (
                                record["charity_number"],
                                ClassificationTypes[k.upper()],
                                classification_record.strip(),
                            )
                        )

        # date fields
        for k, format_ in [
            ("registered_date", "%d/%m/%Y"),
            ("ceased_date", "%d/%m/%Y"),
            ("year_end", "%d/%m/%Y"),
            ("date_annual_return_received", "%d/%m/%Y"),
            ("next_year_end_date", "%d/%m/%Y"),
        ]:
            if record.get(k):
                record[k] = datetime.strptime(record[k], format_).date()
                if record[k] == date(1970, 1, 1):
                    record[k] = None

        # int fields
        for k in [
            "mailing_cycle",
            "most_recent_year_income",
            "most_recent_year_expenditure",
            "donations_and_legacies_income",
            "charitable_activities_income",
            "other_trading_activities_income",
            "investments_income",
            "other_income",
            "raising_funds_spending",
            "charitable_activities_spending",
            "other_spending",
        ]:
            if isinstance(record.get(k), str):
                record[k] = int(record[k])

        # website field
        if record.get("website") and not record.get("website").startswith("http"):
            record["website"] = "http://" + record["website"]

        # postcode field
        if record.get("postcode") == "XX0 0XX":
            record["postcode"] = None
        if record.get("postcode"):
            record["postcode"] = record["postcode"].upper()

        # add charity financial year to list
        if record["year_end"]:
            self.financial_years[(record["charity_number"], record["year_end"])] = {
                k: v for k, v in record.items() if k in fy_fields
            } | {
                "charity_id": record["charity_number"],
            }

        # replace "subject to insolvency proceedings" in charity name
        if insolvency_regex.search(record["charity_name"]):
            record["charity_name"] = re.sub(
                r"\W+$", "", insolvency_regex.sub("", record["charity_name"])
            ).strip()
            if record["notes"]:
                record["notes"] += ". Subject to insolvency proceedings."
            else:
                record["notes"] = "Subject to insolvency proceedings."

        # check whether we have seen this charity before
        if record["charity_number"] in self.charities:
            latest_data = self.charities[record["charity_number"]]
            if (
                latest_data["year_end"]
                and latest_data["year_end"] >= record["year_end"]
            ):
                return
        self.charities[record["charity_number"]] = record

    def save_charities(self):
        db = self._get_db()
        connection = connections[db]

        if self.sample:
            self.logger("Sampling {:,.0f} charities".format(self.sample))
            self.logger("Population of {:,.0f} charities".format(len(self.charities)))
            charity_numbers = random.sample(list(self.charities.keys()), self.sample)
            self.charities = {
                k: v for k, v in self.charities.items() if k in charity_numbers
            }
            self.financial_years = {
                k: v for k, v in self.financial_years.items() if k[0] in charity_numbers
            }
            self.charity_classification = {
                c for c in self.charity_classification if c[0] in charity_numbers
            }
            self.logger("Sampled {:,.0f} charities".format(len(self.charities)))

        with connection.cursor() as cursor, transaction.atomic(using=db):
            # delete existing charities
            Charity.objects.all().delete()

            # insert new charities
            statement = (
                """INSERT INTO "{table}" ("{fields}") VALUES {placeholder};""".format(
                    table=Charity._meta.db_table,
                    fields='", "'.join(char_fields),
                    placeholder="(" + ", ".join(["%s" for f in char_fields]) + ")"
                    if connection.vendor == "sqlite"
                    else "%s",
                )
            )
            self._execute_many(
                cursor,
                statement,
                [[c.get(f) for f in char_fields] for c in self.charities.values()],
            )
            self.logger("Finished table insert [{}]".format(Charity._meta.db_table))

            # insert financial years
            statement = """INSERT INTO "{table}" ("{fields}") VALUES {placeholder}
                    ON CONFLICT(charity_id, year_end) DO UPDATE
                    SET {on_conflict}""".format(
                table=CharityFinancialYear._meta.db_table,
                fields='", "'.join(fy_fields),
                placeholder="(" + ", ".join(["%s" for f in fy_fields]) + ")"
                if connection.vendor == "sqlite"
                else "%s",
                on_conflict=", ".join(
                    (
                        '"{}" = excluded."{}"'.format(f, f)
                        for f in fy_fields
                        if f not in ("charity_id", "year_end")
                    )
                ),
            )
            self._execute_many(
                cursor,
                statement,
                [[c.get(f) for f in fy_fields] for c in self.financial_years.values()],
            )
            self.logger(
                "Finished table insert [{}]".format(CharityFinancialYear._meta.db_table)
            )

            # delete existing charities
            CharityClassification.objects.all().delete()

            # insert new charities
            statement = (
                """INSERT INTO "{table}" ("{fields}") VALUES {placeholder};""".format(
                    table=CharityClassification._meta.db_table,
                    fields='", "'.join(classification_fields),
                    placeholder="("
                    + ", ".join(["%s" for f in classification_fields])
                    + ")"
                    if connection.vendor == "sqlite"
                    else "%s",
                )
            )
            self._execute_many(
                cursor,
                statement,
                tuple(self.charity_classification),
            )
            self.logger(
                "Finished table insert [{}]".format(
                    CharityClassification._meta.db_table
                )
            )
