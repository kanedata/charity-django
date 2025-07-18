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
from charity_django.postcodes.models import GeoCode, GeoEntity, GeoEntityGroup

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    bulk_limit = 50_000
    int_fields = (
        "n_live",
        "n_archived",
        "n_crossborder",
    )
    date_fields = (
        "last_changed",
        "date_introduced",
        "start_date",
    )

    def __init__(self, *args, **kwargs):
        self.debug = None
        super().__init__(*args, **kwargs)
        self.records = defaultdict(dict)
        self.object_count = defaultdict(lambda: 0)
        self.now = datetime.datetime.now()

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

    def handle(self, *args, **options):
        self.debug = options["debug"]
        if self.debug:
            logger.setLevel(logging.DEBUG)
        db = router.db_for_write(GeoCode)
        with transaction.atomic(using=db), connections[db].cursor() as cursor:
            # delete all existing data
            cursor.execute(f'DELETE FROM "{GeoCode._meta.db_table}" WHERE 1=1')
            cursor.execute(f'DELETE FROM "{GeoEntity._meta.db_table}" WHERE 1=1')
            cursor.execute(f'DELETE FROM "{GeoEntityGroup._meta.db_table}" WHERE 1=1')

            # import the new data
            self.set_session(install_cache=options["cache"])

            entity_groups = defaultdict(lambda: set())
            related_entities = {}

            # fetch the file
            data_url = self.get_latest_geoportal_url("PRD_RGC")
            response = self.session.get(data_url)
            zf = zipfile.ZipFile(BytesIO(response.content))
            for filename in zf.namelist():
                if not filename.endswith(".csv"):
                    continue
                reader = csv.DictReader(
                    TextIOWrapper(zf.open(filename), encoding="utf-8-sig")
                )
                field_lookup = {f.verbose_name: f.name for f in GeoEntity._meta.fields}
                for row in tqdm.tqdm(reader):
                    record = {
                        field_lookup.get(k, k): None if v == "n/a" else v.strip()
                        for k, v in row.items()
                        if k in field_lookup
                    }
                    if (
                        row.get("Related entity codes")
                        and row["Related entity codes"] != "n/a"
                    ):
                        related_entities[record["code"]] = [
                            e.strip()
                            for e in row["Related entity codes"].split(",")
                            if e.strip()
                        ]
                    for f in self.int_fields:
                        if record[f]:
                            record[f] = int(record[f].replace(",", ""))
                    for f in self.date_fields:
                        if record[f]:
                            record[f] = datetime.datetime.strptime(
                                record[f], "%d/%m/%Y"
                            ).date()

                    self.add_record(GeoEntity, record)
                self.save_all_records()

                entity_cache = {e.code: e for e in GeoEntity.objects.all()}

            for parent, related in related_entities.items():
                if parent not in entity_cache:
                    continue
                for child in related:
                    if child not in entity_cache:
                        continue
                    entity_cache[parent].related_entities.add(entity_cache[child])
                entity_groups[parent].add(child)
                entity_groups[child].add(parent)

            entity_groups = set(tuple(sorted(g)) for g in entity_groups.values())

            for group in entity_groups:
                group_entities = [entity_cache[e] for e in group]
                group_code = "_".join(sorted(set([e for e in group])))
                group_name = " / ".join(sorted(set([e.name for e in group_entities])))
                group, _ = GeoEntityGroup.objects.update_or_create(
                    code=group_code,
                    defaults=dict(
                        name=group_name,
                    ),
                )
                group.entities.set(group_entities)
            self.save_all_records()

    def parse_row(self, row):
        record = {}
        for k, v in row.items():
            if not k or not isinstance(k, str):
                continue
            if v == "" or v is None:
                record[k] = None
            elif not isinstance(v, str):
                record[k] = v
            elif k in self.date_fields:
                record[k] = None
                try:
                    record[k] = datetime.datetime.strptime(v, "%d/%m/%Y").date()
                except ValueError:
                    record[k] = None
            elif k in self.int_fields:
                record[k] = int(v)
            elif k in self.float_fields:
                record[k] = float(v)
            elif v.endswith("999999"):
                record[k] = None
            elif v in ("9Z9", "Z9"):
                record[k] = None
            else:
                record[k] = v.strip()
        return self.add_record(GeoCode, record)
