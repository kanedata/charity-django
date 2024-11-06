import argparse
import csv
import datetime
import logging
import tempfile
import zipfile
from collections import defaultdict
from io import TextIOWrapper

import tqdm
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections, models, router, transaction
from requests import Session
from requests_cache import CachedSession

from charity_django.postcodes.models import (
    GeoCode,
    Postcode,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

POSTCODES_URL = "https://www.arcgis.com/sharing/rest/content/items/73ce619853044aaaa6f7fa5b90765b85/data"


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

    def __init__(self, *args, **kwargs):
        self.debug = None
        super().__init__(*args, **kwargs)
        self.records = defaultdict(dict)
        self.object_count = defaultdict(lambda: 0)
        self.now = datetime.datetime.now()
        self.postcode_fields = set(
            [f.db_column for f in Postcode._meta.fields]
            + [f.name for f in Postcode._meta.fields]
        )
        self.geocode_cache = {e.GEOGCD: e for e in GeoCode.objects.all()}
        self.geocode_fields = {
            f.db_column: f.name
            for f in Postcode._meta.fields
            if isinstance(f, models.ForeignKey)
        }

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
            "--max-to-import",
            type=int,
            help="Maximum number of records to import",
            default=None,
        )

    def handle(self, *args, **options):
        self.debug = options["debug"]
        db = router.db_for_write(Postcode)
        with transaction.atomic(using=db), connections[db].cursor() as cursor:
            # delete all existing data
            cursor.execute(f'DELETE FROM "{Postcode._meta.db_table}" WHERE 1=1')

            # import the new data
            self.set_session(install_cache=options["cache"])

            # fetch the file
            response = self.session.get(POSTCODES_URL, stream=False)
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(response.content)
                f.close()

                with zipfile.ZipFile(f.name, "r") as zip_ref:
                    record_count = 0
                    for zipped_file in zip_ref.infolist():
                        if not zipped_file.filename.startswith(
                            "Data/multi_csv/"
                        ) or not zipped_file.filename.endswith(".csv"):
                            continue

                        logger.info("Opening {}".format(zipped_file.filename))
                        with zip_ref.open(zipped_file) as csv_file:
                            reader = csv.DictReader(
                                TextIOWrapper(csv_file, "utf-8-sig")
                            )
                            for index, row in tqdm.tqdm(enumerate(reader)):
                                self.parse_row(row)
                                record_count += 1
                                if options.get(
                                    "max_to_import"
                                ) and record_count >= options.get("max_to_import"):
                                    break
                    self.save_all_records()

    def set_session(self, install_cache=False):
        if install_cache:
            logger.info("Using requests_cache")
            self.session = CachedSession(
                cache_name="postcode_cache",
                backend="filesystem",
                cache_control=False,
                expire_after=datetime.timedelta(days=10),
            )
        else:
            self.session = Session()

    def parse_row(self, row):
        record = Postcode()
        for k, v in row.items():
            key = k.strip().upper()
            if key not in self.postcode_fields:
                continue
            value = None
            if v == "" or v is None:
                value = None
            elif k in self.int_fields:
                value = int(v)
            elif k in self.float_fields:
                value = float(v)
            elif v.endswith("999999"):
                value = None
            elif v in ("9Z9", "Z9"):
                value = None
            else:
                value = v.strip()

            if value in self.geocode_cache:
                setattr(
                    record, self.geocode_fields.get(key, key), self.geocode_cache[value]
                )
            else:
                setattr(record, key, value)
        return self.add_record(Postcode, record)

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
        if len(self.records[model]) >= self.bulk_limit:
            self.save_all_records()

    def save_records(self, model):
        logger.info(
            "Saving {:,.0f} {} records".format(len(self.records[model]), model.__name__)
        )
        model.objects.bulk_create(
            self.records[model].values(), batch_size=self.bulk_limit
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
