import argparse
import csv
import datetime
import zipfile
from collections import defaultdict
from io import BytesIO, TextIOWrapper

import tqdm
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections, router, transaction
from requests import Session
from requests_cache import CachedSession

from charity_django.postcodes.models import GeoCode, GeoEntity

CHD_URL = "https://www.arcgis.com/sharing/rest/content/items/393a031178684c69973d0e416a862890/data"


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
            response = self.session.get(CHD_URL)
            zf = zipfile.ZipFile(BytesIO(response.content))

            records = {}

            # change history file
            reader = csv.DictReader(
                TextIOWrapper(zf.open("ChangeHistory.csv"), encoding="utf-8-sig")
            )
            for row in tqdm.tqdm(reader, desc="Reading CSV"):
                record = self.parse_row(row)
                if options["include"] and record["ENTITYCD"] not in options["include"]:
                    continue
                if options["exclude"] and record["ENTITYCD"] in options["exclude"]:
                    continue

                if record["GEOGCD"] not in records:
                    records[record["GEOGCD"]] = []
                records[record["GEOGCD"]].append(record)

            for v in tqdm.tqdm(records.values(), desc="Merging records"):
                self.merge_records(v)

            self.save_all_records()

    def set_session(self, install_cache=False):
        if install_cache:
            self.stdout.write("Using requests_cache")
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
        return record

    def merge_records(self, records):
        records = sorted(records, key=lambda x: x["OPER_DATE"] or self.now)
        record = records[-1]
        record["ENTITYCD"] = self.get_entity(record["ENTITYCD"])
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
        self.stdout.write(
            "Saving {:,.0f} {} records".format(len(self.records[model]), model.__name__)
        )
        model.objects.bulk_create(
            self.records[model].values(),
            batch_size=self.bulk_limit,
            ignore_conflicts=True,
        )
        self.object_count[model] += len(self.records[model])
        self.stdout.write(
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
