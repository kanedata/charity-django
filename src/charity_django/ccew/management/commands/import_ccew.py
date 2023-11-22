# -*- coding: utf-8 -*-
import csv
import io
import zipfile
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

import psycopg2.extras
import requests_cache
import tqdm
from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connections, router, transaction
from django.db.models.fields import BooleanField, DateField

from charity_django.ccew.models import (
    Charity,
    CharityAnnualReturnHistory,
    CharityAreaOfOperation,
    CharityARPartA,
    CharityARPartB,
    CharityClassification,
    CharityEventHistory,
    CharityGoverningDocument,
    CharityOtherNames,
    CharityOtherRegulators,
    CharityPolicy,
    CharityPublishedReport,
    CharityTrustee,
)

from .create_dummy_charity import DUMMY_CHARITY_TYPE

DEFAULT_DATE_FORMAT = "%Y-%m-%d"


class Command(BaseCommand):
    help = "Import CCEW data from a zip file"

    encoding = "utf8"
    base_url = "https://ccewuksprdoneregsadata1.blob.core.windows.net/data/txt/publicextract.{}.zip"
    ccew_file_to_object = {
        "charity": Charity,
        "charity_annual_return_history": CharityAnnualReturnHistory,
        "charity_annual_return_parta": CharityARPartA,
        "charity_annual_return_partb": CharityARPartB,
        "charity_area_of_operation": CharityAreaOfOperation,
        "charity_classification": CharityClassification,
        "charity_event_history": CharityEventHistory,
        "charity_governing_document": CharityGoverningDocument,
        "charity_other_names": CharityOtherNames,
        "charity_other_regulators": CharityOtherRegulators,
        "charity_policy": CharityPolicy,
        "charity_published_report": CharityPublishedReport,
        "charity_trustee": CharityTrustee,
    }
    upsert_files = {
        # conflict target, pre upsert sql
        "charity_annual_return_history": (
            ("organisation_number", "fin_period_end_date", "ar_cycle_reference"),
            None,
        ),
        "charity_annual_return_parta": (
            ("organisation_number", "fin_period_end_date"),
            "UPDATE {table} SET latest_fin_period_submitted_ind = NULL, fin_period_order_number = NULL",
        ),
        "charity_annual_return_partb": (
            ("organisation_number", "fin_period_end_date"),
            "UPDATE {table} SET latest_fin_period_submitted_ind = NULL, fin_period_order_number = NULL",
        ),
    }

    def _get_db(self):
        return router.db_for_write(Charity)

    def logger(self, message, error=False):
        if error:
            self.stderr.write(self.style.ERROR(message))
            return
        self.stdout.write(self.style.SUCCESS(message))

    def handle(self, *args, **options):
        self.temp_dir = TemporaryDirectory()
        self.session = requests_cache.CachedSession(
            "demo_cache.sqlite",
            expire_after=timedelta(days=1),
        )

        db = self._get_db()
        self.connection = connections[db]

        with transaction.atomic():
            # ensure any demonstration charities aren't deleted
            self.demo_charities = list(
                Charity.objects.filter(charity_type=DUMMY_CHARITY_TYPE).values_list(
                    "organisation_number", flat=True
                )
            )
            self.delete_existing()

            self.fetch_file()

        # delete temporary directory
        self.temp_dir.cleanup()

    def _do_upsert(self, filename):
        return (filename in self.upsert_files) and (
            self.connection.vendor == "postgresql"
        )

    def delete_existing(self):
        def delete_table(db_table):
            self.logger(
                "Deleting existing records [{}]".format(db_table._meta.db_table)
            )
            columns = tuple(f.name for f in db_table._meta.fields)
            if "organisation_number" in columns:
                deleted, _ = db_table.objects.exclude(
                    organisation_number__in=self.demo_charities
                ).delete()
            elif "charity" in columns:
                deleted, _ = db_table.objects.exclude(
                    charity_id__in=self.demo_charities
                ).delete()
            self.logger(
                "Deleted {:,.0f} existing records [{}]".format(
                    deleted, db_table._meta.db_table
                )
            )

        for filename, db_table in self.ccew_file_to_object.items():
            if filename == "charity":
                continue
            if self._do_upsert(filename):
                continue
            delete_table(db_table)

        # delete charity records
        delete_table(Charity)

    def fetch_file(self):
        self.files = {}
        for filename in self.ccew_file_to_object:
            url = self.base_url.format(filename)
            self.logger("Fetching: {}".format(url))
            r = self.session.get(url)
            r.raise_for_status()
            self.parse_file(r, filename)

    def parse_file(self, response, filename):
        try:
            z = zipfile.ZipFile(io.BytesIO(response.content))
        except zipfile.BadZipFile:
            self.logger(response.content[0:1000])
            raise
        for f in z.infolist():
            self.logger("Saving: {}".format(f.filename))
            # save the file to a temporary directory
            tmp_file = self.temp_dir.name + "/" + f.filename
            with open(tmp_file, "wb") as out:
                out.write(z.read(f.filename))

            self.process_file(tmp_file, filename)
        z.close()

    def process_file(self, csvfile, filename):
        db_table = self.ccew_file_to_object.get(filename)
        date_fields = [
            f.name for f in db_table._meta.fields if isinstance(f, DateField)
        ]
        bool_fields = [
            f.name for f in db_table._meta.fields if isinstance(f, BooleanField)
        ]
        page_size = 1000

        def get_data(reader, row_count=None):
            for k, row in tqdm.tqdm(enumerate(reader)):
                row = self.clean_fields(row, date_fields, bool_fields)
                if row_count and row_count != len(row):
                    self.logger(row)
                    raise ValueError(
                        "Incorrect number of rows (expected {} and got {})".format(
                            row_count,
                            len(row),
                        )
                    )
                yield list(row.values())

        def get_data_chunks(reader, row_count=None):
            rows = []
            for row in get_data(reader, row_count):
                rows.append(tuple(row))
                if len(rows) == page_size:
                    for r in rows:
                        yield r
                    rows = []
            if rows:
                for r in rows:
                    yield r

        def table_insert(cursor, reader):
            # reset the sequence
            sequence_sql = self.connection.ops.sequence_reset_sql(
                no_style(), [db_table]
            )
            for sql in sequence_sql:
                cursor.execute(sql)

            self.logger("Starting table insert [{}]".format(db_table._meta.db_table))
            fields = list(reader.fieldnames)
            statement = (
                """INSERT INTO "{table}" ("{fields}") VALUES {placeholder}""".format(
                    table=db_table._meta.db_table,
                    fields='", "'.join(fields),
                    placeholder="(" + ", ".join(["%s" for f in fields]) + ")"
                    if self.connection.vendor == "sqlite"
                    else "%s",
                )
            )
            if self.connection.vendor == "postgresql":
                psycopg2.extras.execute_values(
                    cursor,
                    statement,
                    get_data(reader, len(reader.fieldnames)),
                    page_size=page_size,
                )
            else:
                cursor.executemany(
                    statement,
                    get_data_chunks(reader, len(reader.fieldnames)),
                )
            self.logger("Finished table insert [{}]".format(db_table._meta.db_table))

        def table_upsert(cursor, reader):
            self.logger("Starting table upsert [{}]".format(db_table._meta.db_table))
            fields = list(reader.fieldnames)

            # sql to execute prior to upsert
            if self.upsert_files.get(filename)[1]:
                cursor.execute(
                    self.upsert_files.get(filename)[1].format(
                        table=db_table._meta.db_table
                    )
                )

            conflict_target = self.upsert_files.get(filename)[0]
            statement = """INSERT INTO "{table}" ("{fields}") 
                    VALUES %s 
                    ON CONFLICT ("{conflict_target}")
                    DO UPDATE SET {update_fields}""".format(
                table=db_table._meta.db_table,
                fields='", "'.join(fields),
                conflict_target='", "'.join(conflict_target),
                update_fields=", ".join(
                    [
                        '"{field}" = EXCLUDED."{field}"'.format(field=f)
                        for f in fields
                        if f not in conflict_target
                    ]
                ),
            )
            psycopg2.extras.execute_values(
                cursor,
                statement,
                get_data(reader, len(reader.fieldnames)),
                page_size=page_size,
            )
            self.logger("Finished table upsert [{}]".format(db_table._meta.db_table))

        with self.connection.cursor() as cursor:
            with open(csvfile, "r", encoding=self.encoding) as csvfile_handle:
                reader = csv.DictReader(
                    csvfile_handle,
                    delimiter="\t",
                    escapechar="\\",
                    quoting=csv.QUOTE_NONE,
                )
                if self._do_upsert(filename):
                    table_upsert(cursor, reader)
                else:
                    table_insert(cursor, reader)

    def clean_fields(self, record, date_fields=[], bool_fields=[]):
        for f in record.keys():
            # clean blank values
            if record[f] == "":
                record[f] = None

            # clean date fields
            elif f in date_fields and isinstance(record[f], str):
                try:
                    if record.get(f):
                        record[f] = datetime.strptime(
                            record.get(f)[0:10].strip(), "%Y-%m-%d"
                        ).date()
                except ValueError:
                    record[f] = None

            # clean boolean fields
            elif f in bool_fields:
                if isinstance(record[f], str):
                    val = record[f].lower().strip()
                    if val in ["f", "false", "no", "0", "n"]:
                        record[f] = False
                    elif val in ["t", "true", "yes", "1", "y"]:
                        record[f] = True

            # strip string fields
            elif isinstance(record[f], str):
                record[f] = record[f].strip().replace("\x00", "")
        return record
