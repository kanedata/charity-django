import argparse
import csv
import datetime
import logging
import zipfile
from collections import defaultdict
from io import BytesIO, TextIOWrapper

import tqdm
from django.conf import settings
from django.db import connections, router, transaction

from charity_django.postcodes.management.commands._base import BaseCommand
from charity_django.postcodes.models import GeoCode, GeoEntity

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    bulk_limit = 50_000
    int_fields = (
        "USERTYPE",
        "OSEAST1M",
        "OSNRTH1M",
        "OSGRDIND",
        "IMD",
    )
    float_fields = (
        "LAT",
        "LONG",
    )
    date_fields = (
        "OPER_DATE",
        "TERM_DATE",
    )

    def __init__(self, *args, **kwargs):
        self.debug = None
        super().__init__(*args, **kwargs)
        self.records = defaultdict(dict)
        self.object_count = defaultdict(lambda: 0)
        self.now = datetime.datetime.now()
        self.entity_cache = {e.code: e for e in GeoEntity.objects.all()}

    def add_arguments(self, parser):
        parser.add_argument(
            "--cache",
            action=argparse.BooleanOptionalAction,
            help="Cache request",
            default=settings.DEBUG,
        )
        parser.add_argument(
            "--debug",
            action=argparse.BooleanOptionalAction,
            help="Debug",
            default=settings.DEBUG,
        )
        parser.add_argument(
            "--include",
            action="append",
            help="Include only these codes",
            default=[],
        )
        parser.add_argument(
            "--exclude",
            action="append",
            help="Include only these codes",
            default=[],
        )

    def get_entity(self, code):
        if code in self.entity_cache:
            return self.entity_cache[code]

        entity, _ = GeoEntity.objects.get_or_create(code=code)
        self.entity_cache[code] = entity
        return entity

    def handle(self, *args, **options):
        self.debug = options["debug"]
        db = router.db_for_write(GeoCode)
        with transaction.atomic(using=db), connections[db].cursor() as cursor:
            # delete all existing data
            cursor.execute(f'DELETE FROM "{GeoCode._meta.db_table}" WHERE 1=1')

            # import the new data
            self.set_session(install_cache=options["cache"])

            # fetch the file
            data_url = self.get_latest_geoportal_url("PRD_CHD")
            response = self.session.get(data_url)
            zf = zipfile.ZipFile(BytesIO(response.content))

            # change history file
            for encoding in ("utf-8-sig", "windows-1252"):
                reader = csv.DictReader(
                    TextIOWrapper(zf.open("ChangeHistory.csv"), encoding=encoding)
                )
                try:
                    records = {}
                    for row in tqdm.tqdm(
                        reader, desc="Reading CSV with encoding {}".format(encoding)
                    ):
                        record = self.parse_row(row)
                        if options.get("include") and record[
                            "ENTITYCD"
                        ] not in options.get("include", []):
                            continue
                        if options.get("exclude") and record["ENTITYCD"] in options.get(
                            "exclude", []
                        ):
                            continue

                        if record["GEOGCD"] not in records:
                            records[record["GEOGCD"]] = []
                        records[record["GEOGCD"]].append(record)
                    break
                except UnicodeDecodeError:
                    logger.warning(
                        "Failed to read CSV with encoding {}".format(encoding)
                    )
                    continue

            for v in tqdm.tqdm(records.values(), desc="Merging records"):
                self.merge_records(v)

            self.save_all_records()

    def merge_records(self, records):
        records = sorted(records, key=lambda x: x["OPER_DATE"] or self.now)
        record = records[-1]
        record["ENTITYCD"] = self.get_entity(record["ENTITYCD"])
        return self.add_record(GeoCode, record)
