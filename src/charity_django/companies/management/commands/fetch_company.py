import logging
import os
from datetime import datetime

from django.core.management.base import BaseCommand, CommandParser
from requests.exceptions import HTTPError

from charity_django.companies.ch_api import CompaniesHouseAPI
from charity_django.companies.models import Company, SICCode


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Fetches company data from external API"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "company_numbers",
            nargs="+",
            type=str,
            help="Company numbers to fetch data for",
        )
        parser.add_argument(
            "--api-key",
            type=str,
            help="API key to use for fetching data",
            default=os.getenv("CH_API_KEY"),
        )

    def logger(self, message, error=False):
        if error:
            logger.error(message)
            return
        logger.info(message)

    def handle(self, *args, **kwargs):
        self.logger("Fetching company data...")
        api = CompaniesHouseAPI(kwargs["api_key"])

        def check_value(value):
            if value != "" and value is not None:
                return value
            return None

        for company_number in kwargs["company_numbers"]:
            try:
                data = api.get_company(company_number)
            except HTTPError as e:
                self.logger(
                    f"Failed to fetch data for company {company_number}: {e}",
                    error=True,
                )
                continue
            self.logger(f"Fetched data for company {company_number}: {data}")

            updates = dict(
                CompanyName=check_value(data.get("company_name")),
                RegAddress_CareOf=check_value(
                    data.get("registered_office_address", {}).get("care_of")
                ),
                RegAddress_POBox=check_value(
                    data.get("registered_office_address", {}).get("po_box")
                ),
                RegAddress_AddressLine1=check_value(
                    data.get("registered_office_address", {}).get("address_line_1")
                ),
                RegAddress_AddressLine2=check_value(
                    data.get("registered_office_address", {}).get("address_line_2")
                ),
                RegAddress_PostTown=check_value(
                    data.get("registered_office_address", {}).get("locality")
                ),
                RegAddress_County=check_value(
                    data.get("registered_office_address", {}).get("county")
                ),
                RegAddress_Country=check_value(
                    data.get("registered_office_address", {}).get("country")
                ),
                RegAddress_PostCode=check_value(
                    data.get("registered_office_address", {}).get("postal_code")
                ),
                CompanyCategory=check_value(data.get("subtype", data.get("type"))),
                CompanyStatus=check_value(data.get("company_status")),
                CountryOfOrigin=check_value(data.get("jurisdiction")),
                DissolutionDate=check_value(data.get("date_of_cessation")),
                IncorporationDate=check_value(data.get("date_of_creation")),
                Accounts_AccountRefDay=check_value(
                    data.get("accounts", {})
                    .get("accounting_reference_date", {})
                    .get("day")
                ),
                Accounts_AccountRefMonth=check_value(
                    data.get("accounts", {})
                    .get("accounting_reference_date", {})
                    .get("month")
                ),
                Accounts_NextDueDate=check_value(
                    data.get("accounts", {}).get("next_accounts", {}).get("due_on")
                ),
                Accounts_LastMadeUpDate=check_value(
                    data.get("accounts", {}).get("last_accounts", {}).get("made_up_to")
                ),
                Accounts_AccountCategory=check_value(
                    data.get("accounts", {}).get("last_accounts", {}).get("type")
                ),
                Returns_NextDueDate=check_value(
                    data.get("annual_return", {}).get("next_due")
                ),
                Returns_LastMadeUpDate=check_value(
                    data.get("annual_return", {}).get("last_made_up_to")
                ),
                Mortgages_NumMortCharges=None,
                Mortgages_NumMortOutstanding=None,
                Mortgages_NumMortPartSatisfied=None,
                Mortgages_NumMortSatisfied=None,
                LimitedPartnerships_NumGenPartners=None,
                LimitedPartnerships_NumLimPartners=None,
                ConfStmtNextDueDate=check_value(
                    data.get("confirmation_statement", {}).get("next_due")
                ),
                ConfStmtLastMadeUpDate=check_value(
                    data.get("confirmation_statement", {}).get("last_made_up_to")
                ),
                last_updated=now,
            )

            new_category = check_value(data.get("subtype", data.get("type")))
            if new_category != "converted-or-closed":
                updates["CompanyCategory"] = new_category

            now = datetime.now()
            company, created = Company.objects.update_or_create(
                CompanyNumber=company_number, defaults=updates
            )
            self.logger(f"Company created/updated: {company}")

            for name in data.get("previous_company_names", []):
                previous_name, previous_name_created = (
                    company.previous_names.update_or_create(
                        CompanyName=name.get("name"),
                        defaults=dict(
                            ConDate=name.get("effective_from"),
                        ),
                    )
                )
                self.logger(f"Previous company name created/updated: {previous_name}")

            for sic_code in data.get("sic_codes", []):
                try:
                    sic_code_obj, sic_code_created = company.sic_codes.update_or_create(
                        sic_code=SICCode.objects.get(code=sic_code),
                    )
                    self.logger(f"SIC code created/updated: {sic_code_obj}")
                except SICCode.DoesNotExist:
                    self.logger(f"SIC code {sic_code} does not exist", error=True)
                    continue
        self.logger("Company data fetched successfully")
