import csv
import io
import random
import zipfile
from datetime import datetime, timedelta

import requests_cache

from charity_django.ccew.management.commands.import_ccew import (
    Command as ImportCCEWCommand,
)

NUMBER_OF_DUMMY_CHARITIES = 200


class Command(ImportCCEWCommand):
    help = "Create dummy CCEW zip files"
    base_url = "https://ccewuksprdoneregsadata1.blob.core.windows.net/data/txt/publicextract.{}.zip"

    def add_arguments(self, parser):
        parser.add_argument("output_dir", type=str, help="Output directory")

    def handle(self, *args, **options):
        self.session = requests_cache.CachedSession(
            "demo_cache.sqlite",
            expire_after=timedelta(days=1),
        )
        self.output_dir = options["output_dir"]

        self.dummy_charities = set()

        self.fetch_file()

    def parse_file(self, response, filename):
        try:
            z = zipfile.ZipFile(io.BytesIO(response.content))
        except zipfile.BadZipFile:
            self.logger(response.content[0:1000])
            raise
        for f in z.infolist():
            self.logger("Opening: {}".format(f.filename))
            with z.open(f) as csvfile:
                self.process_file(csvfile, filename)
        z.close()

    def process_file(self, csvfile, filename):
        def reg_date(row):
            return int(row["date_of_registration"][0:4])

        def income(row):
            if not row["latest_income"]:
                return 0
            return int(row["latest_income"])

        reader = csv.DictReader(
            io.TextIOWrapper(csvfile, encoding="utf8"),
            delimiter="\t",
            escapechar="\\",
            quoting=csv.QUOTE_NONE,
        )
        if not self.dummy_charities:
            # we'll pick a sample based on five categories
            # - removed and registered before last 5 years
            # - removed and registered in last 5 years
            # - registered and income over £10m
            # - registered and income between £500k and £10m
            # - registered and income under £500k
            now = datetime.now().year
            all_data = [row for row in reader]
            samples = [
                lambda row: (
                    (row["charity_registration_status"] == "Removed")
                    and ((now - reg_date(row)) >= 5)
                ),
                lambda row: (
                    (row["charity_registration_status"] == "Removed")
                    and ((now - reg_date(row)) < 5)
                ),
                lambda row: (
                    (row["charity_registration_status"] != "Removed")
                    and (income(row) < 500_000)
                ),
                lambda row: (
                    (row["charity_registration_status"] != "Removed")
                    and (income(row) >= 10_000_000)
                ),
                lambda row: (
                    (row["charity_registration_status"] != "Removed")
                    and (income(row) >= 500_000)
                    and (income(row) < 10_000_000)
                ),
            ]
            sample_k = int(NUMBER_OF_DUMMY_CHARITIES / 5)
            for sample in samples:
                data_cut = [
                    row["registered_charity_number"] for row in all_data if sample(row)
                ]
                if len(data_cut) < sample_k:
                    sample_k = len(data_cut)
                print(len(data_cut))
                self.dummy_charities.update(
                    random.sample(
                        data_cut,
                        k=sample_k,
                    )
                )
            sample_data = [
                row
                for row in all_data
                if row["registered_charity_number"] in self.dummy_charities
            ]
        else:
            sample_data = [
                row
                for row in reader
                if row["registered_charity_number"] in self.dummy_charities
            ]

        output_zip = zipfile.ZipFile(
            "{}/publicextract.{}.zip".format(self.output_dir, filename), "w"
        )
        output_csv = io.StringIO()
        writer = csv.DictWriter(
            output_csv,
            fieldnames=reader.fieldnames,
            delimiter="\t",
            escapechar="\\",
            quoting=csv.QUOTE_NONE,
        )
        writer.writeheader()
        for row in sample_data:
            writer.writerow(row)
        output_zip.writestr(
            "publicextract.{}.txt".format(filename),
            output_csv.getvalue().encode("utf8"),
        )
