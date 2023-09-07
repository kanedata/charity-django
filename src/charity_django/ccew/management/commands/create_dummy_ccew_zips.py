import csv
import io
import os
import random
import zipfile
from datetime import datetime, timedelta

import requests_cache
from django.utils.text import slugify
from faker import Faker

from charity_django.ccew.management.commands.import_ccew import (
    Command as ImportCCEWCommand,
)
from charity_django.utils.charity_provider import CharityProvider

NUMBER_OF_DUMMY_CHARITIES = 200


class Command(ImportCCEWCommand):
    help = "Create dummy CCEW zip files"
    base_url = "https://ccewuksprdoneregsadata1.blob.core.windows.net/data/txt/publicextract.{}.zip"

    def add_arguments(self, parser):
        parser.add_argument("output_dir", type=str, help="Output directory")

    def handle(self, *args, **options):
        self.fake = Faker("en_GB")
        self.fake.add_provider(CharityProvider)
        self.session = requests_cache.CachedSession(
            "demo_cache.sqlite",
            expire_after=timedelta(days=1),
        )
        self.output_dir = options["output_dir"]

        self.dummy_charities = set()
        self.random_charity = None

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
            now = datetime.now().year
            all_data = [row for row in reader]
            samples = {
                "removed and registered before last 5 years": lambda row: (
                    (row["charity_registration_status"] == "Removed")
                    and ((now - reg_date(row)) >= 5)
                ),
                "removed and registered in last 5 years": lambda row: (
                    (row["charity_registration_status"] == "Removed")
                    and ((now - reg_date(row)) < 5)
                ),
                "registered and income under £500k": lambda row: (
                    (row["charity_registration_status"] != "Removed")
                    and (income(row) < 500_000)
                ),
                "registered and income over £10m": lambda row: (
                    (row["charity_registration_status"] != "Removed")
                    and (income(row) >= 10_000_000)
                ),
                "registered and income between £500k and £10m": lambda row: (
                    (row["charity_registration_status"] != "Removed")
                    and (income(row) >= 500_000)
                    and (income(row) < 10_000_000)
                ),
            }
            sample_k = int(NUMBER_OF_DUMMY_CHARITIES / 5)
            for category, sample in samples.items():
                data_cut = [
                    row["registered_charity_number"] for row in all_data if sample(row)
                ]
                if len(data_cut) < sample_k:
                    sample_k = len(data_cut)
                self.logger(
                    "{}: Choosing {:,.0f} from {:,.0f} records".format(
                        category, sample_k, len(data_cut)
                    )
                )
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
            self.random_charity = random.choice(
                [s for s in sample_data if s["linked_charity_number"] == "0"]
            )
        else:
            sample_data = [
                row
                for row in reader
                if row["registered_charity_number"] in self.dummy_charities
            ]

        if len(sample_data) == 0 and filename == "charity_published_report":
            # create a random report for a charity
            sample_data = [
                {
                    "date_of_extract": self.random_charity["date_of_extract"],
                    "organisation_number": self.random_charity["organisation_number"],
                    "registered_charity_number": self.random_charity[
                        "registered_charity_number"
                    ],
                    "linked_charity_number": self.random_charity[
                        "linked_charity_number"
                    ],
                    "report_name": "STATEMENT OF INQUIRY",
                    "report_location": "https://www.example.com/fake-report-link",
                    "date_published": "2021-11-16",
                }
            ]

        if len(sample_data) == 0:
            msg = "No data for filename: {}".format(filename)
            raise Exception(msg)

        new_filename = os.path.join(
            self.output_dir, "publicextract.{}.zip".format(filename)
        )
        output_zip = zipfile.ZipFile(new_filename, "w")
        self.logger("Writing: {}".format(new_filename))
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
            row = self.parse_row(row)
            writer.writerow(row)
        output_zip.writestr(
            "publicextract.{}.txt".format(filename),
            output_csv.getvalue().encode("utf8"),
        )

    def parse_row(self, row):
        charity_name = self.fake.charity_name() if "charity_name" in row else None

        trustee_name = None
        if "individual_or_organisation" in row:
            if row["individual_or_organisation"] == "O":
                trustee_name = self.fake.company()
            else:
                trustee_name = self.fake.name()

        # replace charity names with dummy names
        field_replacements = [
            ("charity_name", lambda: charity_name),
            ("charity_contact_address1", self.fake.street_address),
            ("charity_contact_address2", self.fake.city),
            ("charity_contact_address3", lambda: ""),
            ("charity_contact_address4", lambda: ""),
            ("charity_contact_address5", lambda: ""),
            ("charity_contact_postcode", self.fake.postcode),
            ("charity_contact_phone", self.fake.phone_number),
            ("charity_contact_email", lambda: f"{slugify(charity_name)}@example.com"),
            (
                "charity_contact_web",
                lambda: f"https://www.example.com/{slugify(charity_name)}",
            ),
            ("charity_company_registration_number", self.fake.company_number),
            ("trustee_name", lambda: trustee_name),
            ("report_location", lambda: "https://www.example.com/fake-report-link"),
            ("charity_activities", self.fake.paragraph),
            ("charity_activities", self.fake.paragraph),
            ("charitable_objects", self.fake.paragraph),
            ("area_of_benefit", self.fake.charity_area_of_benefit),
            ("governing_document_description", self.fake.charity_governing_document),
        ]
        for field, replacement in field_replacements:
            if row.get(field):
                row[field] = replacement()
        return row
