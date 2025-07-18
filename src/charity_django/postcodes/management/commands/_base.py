import datetime
import logging

from django.core.management.base import BaseCommand
from requests import Session
from requests_cache import CachedSession

GEOPORTAL_API_URL = "https://hub.arcgis.com/api/search/v1/collections/all/items"
GEOPORTAL_DATA_URL = "https://www.arcgis.com/sharing/rest/content/items/{}/data"


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BaseCommand(BaseCommand):
    def get_latest_geoportal_url(self, product_code: str) -> str:
        """
        Returns the latest URL for a given product code.
        """
        print(f"Fetching latest URL for product code: {product_code}")
        api_response = self.session.get(
            GEOPORTAL_API_URL,
            params={"q": product_code, "sortBy": "-properties.created"},
        )
        api_response.raise_for_status()
        item = api_response.json()["features"][0]["id"]
        url = GEOPORTAL_DATA_URL.format(item)
        print(f"Latest URL for product code {product_code}: {url}")
        return url

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
        return record

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
