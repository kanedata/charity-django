# -*- coding: utf-8 -*-
import csv
import logging
from collections import defaultdict
from datetime import timedelta
from io import StringIO

import requests_cache
from django.core.management.base import BaseCommand
from django.db import router

from charity_django.ccew.models import (
    CharityAreaOfOperation,
    CharityAreaOfOperationLookup,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_DATE_FORMAT = "%Y-%m-%d"


class Command(BaseCommand):
    help = "Update Area of Operation Lookups"

    def _get_db(self):
        return router.db_for_write(CharityAreaOfOperationLookup)

    def logger(self, message, error=False):
        if error:
            logger.error(message)
            return
        logger.info(message)

    def add_arguments(self, parser):
        parser.add_argument("--sample", type=int, default=0)

    def handle(self, *args, **options):
        # fetch all existing area of operations
        self.logger("Fetching existing Area of Operations")
        areas = set(
            list(
                CharityAreaOfOperation.objects.values_list(
                    "geographic_area_type", "geographic_area_description"
                ).distinct()
            )
            + list(
                CharityAreaOfOperation.objects.filter(
                    parent_geographic_area_description__isnull=False
                )
                .values_list(
                    "parent_geographic_area_type", "parent_geographic_area_description"
                )
                .distinct()
            )
        )
        existing_areas = CharityAreaOfOperationLookup.objects.values_list(
            "geographic_area_type", "geographic_area_description"
        ).distinct()
        for area in areas:
            if area not in existing_areas:
                CharityAreaOfOperationLookup.objects.get_or_create(
                    geographic_area_type=area[0],
                    geographic_area_description=area[1],
                )
        self.logger(f"Found {len(areas)} existing Area of Operations")

        # fetch lookups
        session = requests_cache.CachedSession(
            "demo_cache.sqlite",
            expire_after=timedelta(days=1),
        )
        response = session.get(
            "https://raw.githubusercontent.com/drkane/charity-lookups/refs/heads/master/cc-aoo-gss-iso-new.csv"
        )
        response.raise_for_status()
        self.logger("Fetched Area of Operations lookups from remote source")

        # parse CSV
        csv_data = StringIO(response.content.decode("utf-8-sig"))
        reader = csv.DictReader(csv_data)
        self.logger("Parsing Area of Operations lookups")
        results = {
            "total": 0,
            "created": 0,
            "updated": 0,
            "errors": 0,
        }
        areas = defaultdict(list)
        for row in reader:
            if not row["geographic_area_description"]:
                continue
            areas[
                (row["geographic_area_type"], row["geographic_area_description"])
            ].append(row)

        for area_info, rows in areas.items():
            if len(rows) > 1:
                self.logger(
                    f"Warning: Multiple rows found for area '{area_info[1]}'. "
                    "Deleting rather than updating.",
                    error=True,
                )
                CharityAreaOfOperationLookup.objects.filter(
                    geographic_area_type=area_info[0].strip(),
                    geographic_area_description=area_info[1].strip(),
                ).delete()
                for row in rows:
                    area = CharityAreaOfOperationLookup.objects.create(
                        geographic_area_type=area_info[0].strip(),
                        geographic_area_description=area_info[1].strip(),
                        gss=row.get("GSS", "").strip() or None,
                        iso3166_1=row.get("ISO3166-1", "").strip() or None,
                        iso3166_1_alpha3=row.get("ISO3166-1:3", "").strip() or None,
                        iso3166_2_gb=row.get("ISO3166-2:GB", "").strip() or None,
                        continent=row.get("ContinentCode", "").strip() or None,
                    )
                    results["created"] += 1
                    results["total"] += 1
                continue
            row = rows[0]
            area, created = CharityAreaOfOperationLookup.objects.update_or_create(
                geographic_area_type=area_info[0].strip(),
                geographic_area_description=area_info[1].strip(),
                defaults={
                    "gss": row.get("GSS", "").strip() or None,
                    "iso3166_1": row.get("ISO3166-1", "").strip() or None,
                    "iso3166_1_alpha3": row.get("ISO3166-1:3", "").strip() or None,
                    "iso3166_2_gb": row.get("ISO3166-2:GB", "").strip() or None,
                    "continent": row.get("ContinentCode", "").strip() or None,
                },
            )
            if created:
                results["created"] += 1
            else:
                results["updated"] += 1
            results["total"] += 1
        self.logger(
            f"Processed {results['total']} Area of Operations lookups: "
            f"{results['created']} created, {results['updated']} updated"
        )

        for area in CharityAreaOfOperationLookup.objects.filter(
            gss__isnull=True,
            iso3166_1__isnull=True,
            iso3166_1_alpha3__isnull=True,
            iso3166_2_gb__isnull=True,
            continent__isnull=True,
        ):
            self.logger(
                f"Area of Operation {area.geographic_area_description} has no GSS or ISO codes",
                error=True,
            )
