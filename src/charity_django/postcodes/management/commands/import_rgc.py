import argparse
import csv
import datetime
import logging
import zipfile
from collections import defaultdict
from io import BytesIO, TextIOWrapper

import tqdm
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections, router, transaction
from requests import Session
from requests_cache import CachedSession

from charity_django.postcodes.models import GeoCode, GeoEntity, GeoEntityGroup

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

RGC_URL = "https://www.arcgis.com/sharing/rest/content/items/34f4b9d554324bc494dc406dca58001a/data"


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
            response = self.session.get(RGC_URL)
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

    def set_session(self, install_cache=False):
        if install_cache:
            logger.info("Using requests_cache")
            self.session = CachedSession(
                cache_name="postcode_cache",
                cache_control=False,
                expire_after=datetime.timedelta(days=10),
            )
        else:
            self.session = Session()

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

    def add_record(self, model, record):
        if isinstance(record, dict):
            record = model(**record)
        if model._meta.unique_together:
            unique_fields = tuple(
                getattr(record, f) for f in model._meta.unique_together[0]
            )
        else:
            unique_fields = (record.pk,)
        self.records[model][unique_fields] = record
        if len(self.records[GeoCode]) >= self.bulk_limit:
            self.save_all_records()

    def save_records(self, model):
        logger.info(
            "Saving {:,.0f} {} records".format(len(self.records[model]), model.__name__)
        )
        model.objects.bulk_create(
            self.records[model].values(),
            batch_size=self.bulk_limit,
            ignore_conflicts=True,
        )
        self.object_count[model] += len(self.records[model])
        logger.info(
            "Saved {:,.0f} {} records ({:,.0f} total)".format(
                len(self.records[model]),
                model.__name__,
                self.object_count[model],
            )
        )
        self.records[model] = {}

    def save_all_records(self):
        for model, records in self.records.items():
            if len(records):
                self.save_records(model)
