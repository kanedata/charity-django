import csv
import re
from datetime import datetime, timedelta
from io import StringIO

import tqdm
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from charity_django.ccew.models import Charity, Merger
from charity_django.utils.cachedsession import CachedHTMLSession

# updated version of https://gist.github.com/drkane/0faa257e447452661a4d

# default location of the register of mergers
ROM_PAGE = "https://www.gov.uk/government/publications/register-of-merged-charities"


class Command(BaseCommand):
    help = "Import Register of Mergers"
    base_url = "https://www.gov.uk/government/publications/register-of-merged-charities"
    columns = {
        "Name of transferring charity (transferor) and charity number (if any)": "transferor_name",
        "Name of receiving charity (transferee) and charity number (if any)": "transferee_name",
        "Date Vesting Declaration made": "date_vesting_declaration",
        "Date property transferred": "date_property_transferred",
        "Date merger registered": "date_merger_registered",
    }
    row_separator = re.compile(r"\s\s\s\s+", re.MULTILINE)
    regno_regex = re.compile(r"(\(([0-9]{6,7})([\-\/]([0-9]+))?\)| ([0-9]{6,7})$)")
    date_fields = [
        "date_vesting_declaration",
        "date_property_transferred",
        "date_merger_registered",
    ]
    date_formats = [
        "%d/%m/%Y",
        "%d-%b-%y",
        "%d/%m/%y",
        "%d-%b-%Y",
    ]
    charity_number_typos = {
        # (From, To),
        "1115638": "1112538",  # Dauntsey's School (1115638)
        "1076829": "1076289",  # Jo's Trust (1076829)
        "2110169": "210169",  # The Joseph Rowntree Foundation (2110169)
        "1097529": "1096480",  # 2GETHER NHS FOUNDATION TRUST CHARITABLE FUND AND OTHER RELATED CHARITIES (1097529)
        "176414": "1076414",  # Royal Hospital Chelsea Appeal Limited (176414)
        "2101693": "210169",  # The Joseph Rowntree Housing Trust (2101693)
        "114799": "1147994",  # The Truell Conservation Foundation (114799)
        "116891": "1168691",  # MERRYLEGS ASSISTED RIDING FOR CHILDREN WITH ADDITIONAL NEEDS (116891)
        "117420": "1177420",  # SUSSEX MASONIC CHARITABLE FOUNDATION, CIO (117420)
        "106008": "1060008",  # The Co-Operative College (106008)
        # THE LEES CHAPEL (3967948)
        # CENTRAL BAPTIST CHURCH WALTHAMSTOW (4059023)
        # THE ECCLESIASTICAL PARISH COUNCIL OF SAINT STEPHEN, BUSH HILL PARK (4061834)
        # COLDSTREAM GUARDS CHATTELS CHARITY (3984623)
        # KING'S WAY COMMUNITY CHURCH (3963762)
        # DERBY TOWN MISSION (4049329)
        # Downside Abbey General Trust (1158507-1)
        # Courtauld Institute of Art (3991797)
        # EBENEZER CHAPEL TRUST (4060412) (Excepted Charity)
        # PARKSTONE EVANGELICAL FREE CHURCH AND TRUST PROPERTY (3010118)
        # Chelsea And Westminster Health Charity (1067412)
        # Leeds Teaching Hospitals Charitable Fund (1075308-3)
        # Board of Trustees of the Science Museum (000000)
        # The Primary Immunodeficiency Association (893217)
        # Learning and Skills Network (LSN) (113456)
        # The Community Foundation for Wiltshire & Swindon (123126)
        # Christ Church (United Reformed) Leatherhead - Student Fund (234688)
        # 96.3 Radio Aire & Magic 828's Cash for Kids (119842)
        # Henry Smith's or Poyle Charity (1078131)
        # The Nomad Trust (1127184)
        # The University of Reading (4037741)
        # Clatterbridge Cancer Campaign (4020519)
        # Hightown Praetorian and Churches Housing Association (4040555)
        # Yorkshire Housing Limited (4038784)
    }

    def logger(self, message, error=False):
        if error:
            self.stderr.write(self.style.ERROR(message))
            return
        self.stdout.write(self.style.SUCCESS(message))

    def handle(self, *args, **options):
        self.session = CachedHTMLSession(
            "demo_cache.sqlite",
            expire_after=timedelta(days=1),
        )
        self.charity_cache = {}

        self.fetch_file()
        with transaction.atomic():
            for filename, response in self.files.items():
                self.parse_file(response, filename)

    def lookup_charity(self, regno, subno):
        key = (regno, subno)
        if key in self.charity_cache:
            return self.charity_cache[key]

        charity = Charity.objects.filter(
            registered_charity_number=regno, linked_charity_number=subno
        ).first()
        if charity:
            self.charity_cache[key] = charity
            return self.charity_cache[key]

        self.charity_cache[key] = Charity.objects.filter(
            organisation_number=regno
        ).first()

        return self.charity_cache[key]

    def clean_fields(self, record, bool_fields=[]):
        record = {self.columns.get(k.strip(), k): v for k, v in record.items()}

        for f in record.keys():
            # clean blank values
            if record[f] == "":
                record[f] = None

            # clean date fields
            elif f in self.date_fields and isinstance(record[f], str):
                parsed_value = None
                date_value = record.get(f)[0:10].strip()
                for date_format in self.date_formats:
                    try:
                        parsed_value = datetime.strptime(date_value, date_format)
                        break
                    except ValueError:
                        continue
                if not parsed_value:
                    self.logger(
                        "Could not parse date: {}".format(date_value), error=True
                    )
                record[f] = parsed_value

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

    def fetch_file(self):
        """
        Find the latest register of mergers on a page
        """
        r = self.session.get(self.base_url)
        self.files = {
            "rom": self.session.get(
                next(l for l in r.html.absolute_links if l.endswith(".csv"))
            )
        }

    def get_rows(self, response):
        reader = csv.DictReader(StringIO(response.content.decode("latin_1")))
        for row in reader:
            # skip blank rows
            if all([v == "" for v in row.values()]):
                continue

            row = self.clean_fields(row)

            # split the transferor name
            split_values = self.row_separator.split(row["transferor_name"])
            for value in split_values:
                yield {
                    **row,
                    "transferor_name": value.strip(),
                }

    def get_charity_numbers(self, row):
        for field in ["transferor", "transferee"]:
            original_field = row[f"{field}_name"]
            row[f"{field}_regno"] = None
            row[f"{field}_subno"] = None
            regno = self.regno_regex.search(original_field)
            if regno:
                if regno.group(2):
                    row[f"{field}_regno"] = regno.group(2)
                    row[f"{field}_subno"] = regno.group(4) or 0
                elif regno.group(5):
                    row[f"{field}_regno"] = regno.group(5)
                    row[f"{field}_subno"] = 0
                else:
                    self.logger(
                        "No charity number found for: {} [{}]".format(
                            original_field,
                            regno.groups(),
                        ),
                        error=True,
                    )
                    continue
                row[f"{field}_regno"] = self.charity_number_typos.get(
                    row[f"{field}_regno"], row[f"{field}_regno"]
                )
                if isinstance(row[f"{field}_subno"], str):
                    row[f"{field}_subno"] = row[f"{field}_subno"].lstrip("0")
                    if row[f"{field}_subno"] == "":
                        row[f"{field}_subno"] = 0
                    else:
                        row[f"{field}_subno"] = int(row[f"{field}_subno"])
                row[f"{field}_name"] = self.regno_regex.sub("", original_field).strip()

                # add the organisation number
                row[field] = self.lookup_charity(
                    row[f"{field}_regno"],
                    row[f"{field}_subno"],
                )

                if not row[field]:
                    self.logger(f"Could not find charity: {original_field}", error=True)

        return row

    def parse_file(self, response, filename):
        mergers = []
        for row in tqdm.tqdm(self.get_rows(response)):
            row = self.get_charity_numbers(row)
            mergers.append(Merger(**row))
        # delete existing mergers
        Merger.objects.all().delete()
        # save new mergers
        Merger.objects.bulk_create(mergers)
