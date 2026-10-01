import argparse
import csv
import datetime
import logging
import re
import tempfile
import warnings
import zipfile
from collections import defaultdict
from io import TextIOWrapper

import tqdm
from django.conf import settings
from django.db import connections, models, router, transaction

from charity_django.postcodes.management.commands._base import BaseCommand
from charity_django.postcodes.models import (
    GeoCode,
    Postcode,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

POSTCODE_FILE_FIELDS = {
    "pcd7": "PCD",
    "pcd8": "PCD2",
    "pcds": "PCDS",
    "dointr": "DOINTR",
    "doterm": "DOTERM",
    "usrtypind": "USERTYPE",
    "east1m": "OSEAST1M",
    "north1m": "OSNRTH1M",
    "gridind": "OSGRDIND",
    "oa21cd": "OA21",
    "ctyXXcd": "CTY",
    "cedXXcd": "CED",
    "ladXXcd": "LAUA",
    "wdXXcd": "WARD",
    "nhserXXcd": "NHSER",
    "ctryXXcd": "CTRY",
    "rgnXXcd": "RGN",
    "pconXXcd": "PCON",
    "ttwaXXcd": "TTWA",
    "itlXXcd": "ITL",
    "nparkXXcd": "PARK",
    "lsoa21cd": "LSOA21",
    "msoa21cd": "MSOA21",
    "wz11cd": "WZ11",
    "sicblXXcd": "SICBL",
    "bua24cd": "BUA11",
    "ruc21ind": "RU21IND",
    "oac11ind": "OAC11",
    "oac21ind": "OAC21",
    "lat": "LAT",
    "long": "LONG",
    "lepXXcd1": "LEP1",
    "lepXXcd2": "LEP2",
    "pfaXXcd": "PFA",
    "imdXXind": "IMD",
    "icbXXcd": "ICB",
}


"""
Fields no longer included:
- HLTHAU
- EER
- TECLEC
- LSOA11
- MSOA11
- PCT
- BUASD11
- CALNCV
- OA11
"""


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
            data_url = self.get_latest_geoportal_url("PRD_NSPL")
            response = self.session.get(data_url, stream=False)
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
                            new_fieldnames = []
                            mismatch = []

                            for f in reader.fieldnames:
                                new_f = f.strip().lower()
                                new_f_xx = re.sub(r"[0-9]{2}", "XX", new_f)
                                if new_f in POSTCODE_FILE_FIELDS:
                                    new_fieldnames.append(new_f)
                                elif new_f_xx in POSTCODE_FILE_FIELDS:
                                    new_fieldnames.append(new_f_xx)
                                else:
                                    new_fieldnames.append(new_f)
                                    mismatch.append(f"Unrecognized field: {f}")

                            reader.fieldnames = new_fieldnames
                            if reader.fieldnames != list(POSTCODE_FILE_FIELDS.keys()):
                                error = False
                                for field in reader.fieldnames:
                                    if field not in POSTCODE_FILE_FIELDS:
                                        mismatch.append(f"Extra field: {field}")
                                        error = True
                                for field in POSTCODE_FILE_FIELDS:
                                    if field not in reader.fieldnames:
                                        mismatch.append(f"Missing field: {field}")
                                msg = "Field mismatch: {}".format("\n".join(mismatch))
                                if error:
                                    raise ValueError(msg)
                                else:
                                    warnings.warn(msg)
                            reader.fieldnames = [
                                POSTCODE_FILE_FIELDS[f] for f in reader.fieldnames
                            ]

                            for index, row in tqdm.tqdm(enumerate(reader)):
                                self.parse_row(row)
                                record_count += 1
                                if options.get(
                                    "max_to_import"
                                ) and record_count >= options.get("max_to_import"):
                                    break
                    self.save_all_records()

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
