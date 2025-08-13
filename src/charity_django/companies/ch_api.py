from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime as DateTime
from enum import Enum

import requests
from dateutil.parser import isoparse


class FileTypes(Enum):
    IXBRL = "application/xhtml+xml"
    XBRL = "application/xml"
    JSON = "application/json"
    CSV = "text/csv"
    PDF = "application/pdf"


class AccountTypes(Enum):
    NULL = "null"  # "Null"
    FULL = "full"  # "Full"
    SMALL = "small"  # "Small"
    MEDIUM = "medium"  # "Medium"
    GROUP = "group"  # "Group"
    DORMANT = "dormant"  # "Dormant"
    INTERIM = "interim"  # "Interim"
    INITIAL = "initial"  # "Initial"
    TOTAL_EXEMPTION_FULL = "total-exemption-full"  # "Total Exemption Full"
    TOTAL_EXEMPTION_SMALL = "total-exemption-small"  # "Total Exemption Small"
    PARTIAL_EXEMPTION = "partial-exemption"  # "Partial Exemption"
    AUDIT_EXEMPTION_SUBSIDIARY = (
        "audit-exemption-subsidiary"  # "Audit Exemption Subsidiary"
    )
    FILING_EXEMPTION_SUBSIDIARY = (
        "filing-exemption-subsidiary"  # "Filing Exemption Subsidiary"
    )
    MICRO_ENTITY = "micro-entity"  # "Micro Entity"
    NO_ACCOUNTS_TYPE_AVAILABLE = (
        "no-accounts-type-available"  # "No accounts type available"
    )
    AUDITED_ABRIDGED = "audited-abridged"  # "Audited abridged"
    UNAUDITED_ABRIDGED = "unaudited-abridged"  # "Unaudited abridged"
    NO_ACCOUNTS_FILED = "no-accounts-filed"  # "Unaudited abridged"


"""
Lookup for converting from CSV Download to AccountTypes
"""
ACCOUNTS_TYPE_LOOKUP = {
    "ACCOUNTS TYPE NOT AVAILABLE": AccountTypes.NO_ACCOUNTS_TYPE_AVAILABLE,
    "AUDIT EXEMPTION SUBSIDIARY": AccountTypes.AUDIT_EXEMPTION_SUBSIDIARY,
    "AUDITED ABRIDGED": AccountTypes.AUDITED_ABRIDGED,
    "DORMANT": AccountTypes.DORMANT,
    "FILING EXEMPTION SUBSIDIARY": AccountTypes.FILING_EXEMPTION_SUBSIDIARY,
    "FULL": AccountTypes.FULL,
    "GROUP": AccountTypes.GROUP,
    "MEDIUM": AccountTypes.MEDIUM,
    "MICRO ENTITY": AccountTypes.MICRO_ENTITY,
    "SMALL": AccountTypes.SMALL,
    "TOTAL EXEMPTION FULL": AccountTypes.TOTAL_EXEMPTION_FULL,
    "TOTAL EXEMPTION SMALL": AccountTypes.TOTAL_EXEMPTION_SMALL,
    "UNAUDITED ABRIDGED": AccountTypes.UNAUDITED_ABRIDGED,
    "NO ACCOUNTS FILED": AccountTypes.NO_ACCOUNTS_FILED,
    "INITIAL": AccountTypes.INITIAL,
    "PARTIAL EXEMPTION": AccountTypes.PARTIAL_EXEMPTION,
}


class CompanyStatuses(Enum):
    ACTIVE = "active"  # , "Active"
    ACTIVE_PROPOSAL_TO_STRIKE_OFF = "active-proposal-to-strike-off"  # , "Active"
    DISSOLVED = "dissolved"  # , "Dissolved"
    LIQUIDATION = "liquidation"  # , "Liquidation"
    RECEIVERSHIP = "receivership"  # , "Receivership"
    ADMINISTRATION = "administration"  # , "Administration"
    VOLUNTARY_ARRANGEMENT = "voluntary-arrangement"  # , "Voluntary arrangement"
    CONVERTED_CLOSED = "converted-closed"  # , "Converted/Closed"
    INSOLVENCY_PROCEEDINGS = "insolvency-proceedings"  # , "Insolvency proceedings"
    REGISTERED = "registered"  # , "Registered"
    REMOVED = "removed"  # , "Removed"
    CLOSED = "closed"  # , "Closed"
    OPEN = "open"  # , "Open"


COMPANY_STATUS_LOOKUP = {
    "Active": CompanyStatuses.ACTIVE,
    "Active - Proposal to Strike off": CompanyStatuses.ACTIVE_PROPOSAL_TO_STRIKE_OFF,
    "ADMINISTRATION ORDER": CompanyStatuses.ADMINISTRATION,
    "ADMINISTRATIVE RECEIVER": CompanyStatuses.ADMINISTRATION,
    "In Administration": CompanyStatuses.ADMINISTRATION,
    "In Administration/Administrative Receiver": CompanyStatuses.ADMINISTRATION,
    "In Administration/Receiver Manager": CompanyStatuses.ADMINISTRATION,
    "Liquidation": CompanyStatuses.LIQUIDATION,
    "Live but Receiver Manager on at least one charge": CompanyStatuses.RECEIVERSHIP,
    "RECEIVER MANAGER / ADMINISTRATIVE RECEIVER": CompanyStatuses.RECEIVERSHIP,
    "RECEIVERSHIP": CompanyStatuses.RECEIVERSHIP,
    "Voluntary Arrangement": CompanyStatuses.VOLUNTARY_ARRANGEMENT,
    "VOLUNTARY ARRANGEMENT / ADMINISTRATIVE RECEIVER": CompanyStatuses.VOLUNTARY_ARRANGEMENT,
    "VOLUNTARY ARRANGEMENT / RECEIVER MANAGER": CompanyStatuses.VOLUNTARY_ARRANGEMENT,
}


class CompanyTypes(Enum):
    PRIVATE_UNLIMITED = "private-unlimited"  # , "Private unlimited company"
    LTD = "ltd"  # , "Private limited company"
    PLC = "plc"  # , "Public limited company"
    OLD_PUBLIC_COMPANY = "old-public-company"  # , "Old public company"
    PRIVATE_LIMITED_GUARANT_NSC_LIMITED_EXEMPTION = "private-limited-guarant-nsc-limited-exemption"  # "Private Limited Company by guarantee without share capital, use of 'Limited' exemption"
    LIMITED_PARTNERSHIP = "limited-partnership"  # , "Limited partnership"
    PRIVATE_LIMITED_GUARANT_NSC = "private-limited-guarant-nsc"  # , "Private limited by guarantee without share capital",
    CONVERTED_OR_CLOSED = "converted-or-closed"  # , "Converted / closed"
    PRIVATE_UNLIMITED_NSC = (
        "private-unlimited-nsc"  # "Private unlimited company without share capital",
    )
    PRIVATE_LIMITED_SHARES_SECTION_30_EXEMPTION = "private-limited-shares-section-30-exemption"  # "Private Limited Company, use of 'Limited' exemption",
    PROTECTED_CELL_COMPANY = "protected-cell-company"  # , "Protected cell company"
    ASSURANCE_COMPANY = "assurance-company"  # , "Assurance company"
    OVERSEA_COMPANY = "oversea-company"  # , "Overseas company"
    EEIG_ESTABLISHMENT = "eeig-establishment"  # "European Economic Interest Grouping Establishment (EEIG)",
    ICVC_SECURITIES = "icvc-securities"  # , "Investment company with variable capital"
    ICVC_WARRANT = "icvc-warrant"  # , "Investment company with variable capital"
    ICVC_UMBRELLA = "icvc-umbrella"  # , "Investment company with variable capital"
    REGISTERED_SOCIETY_NON_JURISDICTIONAL = (
        "registered-society-non-jurisdictional"  # , "Registered society",
    )
    INDUSTRIAL_AND_PROVIDENT_SOCIETY = (
        "industrial-and-provident-society"  # "Industrial and Provident society",
    )
    NORTHERN_IRELAND = "northern-ireland"  # , "Northern Ireland company"
    NORTHERN_IRELAND_OTHER = (
        "northern-ireland-other"  # , "Credit union (Northern Ireland)",
    )
    LLP = "llp"  # , "Limited liability partnership"
    ROYAL_CHARTER = "royal-charter"  # , "Royal charter company"
    INVESTMENT_COMPANY_WITH_VARIABLE_CAPITAL = "investment-company-with-variable-capital"  # "Investment company with variable capital",
    UNREGISTERED_COMPANY = "unregistered-company"  # , "Unregistered company"
    OTHER = "other"  # , "Other company type"
    EUROPEAN_PUBLIC_LIMITED_LIABILITY_COMPANY_SE = "european-public-limited-liability-company-se"  # "European public limited liability company (SE)",
    UNITED_KINGDOM_SOCIETAS = "united-kingdom-societas"  # , "United Kingdom Societas"
    UK_ESTABLISHMENT = "uk-establishment"  # , "UK establishment company"
    SCOTTISH_PARTNERSHIP = "scottish-partnership"  # , "Scottish qualifying partnership"
    CHARITABLE_INCORPORATED_ORGANISATION = "charitable-incorporated-organisation"  # "Charitable incorporated organisation",
    SCOTTISH_CHARITABLE_INCORPORATED_ORGANISATION = "scottish-charitable-incorporated-organisation"  # "Scottish charitable incorporated organisation",
    FURTHER_EDUCATION_OR_SIXTH_FORM_COLLEGE_CORPORATION = "further-education-or-sixth-form-college-corporation"  # "Further education or sixth form college corporation",
    EEIG = "eeig"  # , "European Economic Interest Grouping (EEIG)"
    UKEIG = "ukeig"  # , "United Kingdom Economic Interest Grouping"
    REGISTERED_OVERSEAS_ENTITY = "registered-overseas-entity"  # , "Overseas entity"
    COMMUNITY_INTEREST_COMPANY = (
        "community-interest-company"  # "Community Interest Company (CIC)",
    )
    PRIVATE_FUND_LIMITED_PARTNERSHIP = (
        "private-fund-limited-partnership"  # "Private Fund Limited Partnership (PFLP)",
    )
    AUTHORISED_COMPANY_SERVICE_PROVIDER = (
        "authorised-company-service-provider"  # "Authorised Company Service Provider",
    )


CLG_TYPES = [
    CompanyTypes.PRIVATE_LIMITED_GUARANT_NSC,
    CompanyTypes.PRIVATE_LIMITED_GUARANT_NSC_LIMITED_EXEMPTION,
]
NONPROFIT_TYPES = CLG_TYPES + [
    CompanyTypes.COMMUNITY_INTEREST_COMPANY,
    CompanyTypes.PRIVATE_UNLIMITED_NSC,
    CompanyTypes.REGISTERED_SOCIETY_NON_JURISDICTIONAL,
    CompanyTypes.INDUSTRIAL_AND_PROVIDENT_SOCIETY,
    CompanyTypes.ROYAL_CHARTER,
    CompanyTypes.CHARITABLE_INCORPORATED_ORGANISATION,
    CompanyTypes.SCOTTISH_CHARITABLE_INCORPORATED_ORGANISATION,
]

COMPANY_CATEGORY_LOOKUP = {
    "Community Interest Company": CompanyTypes.COMMUNITY_INTEREST_COMPANY,
    "Charitable Incorporated Organisation": CompanyTypes.CHARITABLE_INCORPORATED_ORGANISATION,
    "PRI/LTD BY GUAR/NSC (Private, limited by guarantee, no share capital)": CompanyTypes.PRIVATE_LIMITED_GUARANT_NSC,
    "PRI/LBG/NSC (Private, Limited by guarantee, no share capital, use of 'Limited' exemption)": CompanyTypes.PRIVATE_LIMITED_GUARANT_NSC_LIMITED_EXEMPTION,
    "Converted/Closed": CompanyTypes.CONVERTED_OR_CLOSED,
    "European Public Limited-Liability Company (SE)": CompanyTypes.EUROPEAN_PUBLIC_LIMITED_LIABILITY_COMPANY_SE,
    "Investment Company with Variable Capital": CompanyTypes.INVESTMENT_COMPANY_WITH_VARIABLE_CAPITAL,
    "Investment Company with Variable Capital (Securities)": CompanyTypes.ICVC_SECURITIES,
    "Investment Company with Variable Capital(Umbrella)": CompanyTypes.ICVC_UMBRELLA,
    "Industrial and Provident Society": CompanyTypes.INDUSTRIAL_AND_PROVIDENT_SOCIETY,
    "Limited Partnership": CompanyTypes.LIMITED_PARTNERSHIP,
    "Limited Liability Partnership": CompanyTypes.LLP,
    "Old Public Company": CompanyTypes.OLD_PUBLIC_COMPANY,
    "Other company type": CompanyTypes.OTHER,
    "Public Limited Company": CompanyTypes.PLC,
    "Private Limited Company": CompanyTypes.LTD,
    "PRIV LTD SECT. 30 (Private limited company, section 30 of the Companies Act)": CompanyTypes.PRIVATE_LIMITED_SHARES_SECTION_30_EXEMPTION,
    "Private Unlimited": CompanyTypes.PRIVATE_UNLIMITED,
    "Private Unlimited Company": CompanyTypes.PRIVATE_UNLIMITED,
    "Protected Cell Company": CompanyTypes.PROTECTED_CELL_COMPANY,
    "Royal Charter Company": CompanyTypes.ROYAL_CHARTER,
    "Registered Society": CompanyTypes.REGISTERED_SOCIETY_NON_JURISDICTIONAL,
    "Scottish Charitable Incorporated Organisation": CompanyTypes.SCOTTISH_CHARITABLE_INCORPORATED_ORGANISATION,
    "Scottish Partnership": CompanyTypes.SCOTTISH_PARTNERSHIP,
    "United Kingdom Economic Interest Grouping": CompanyTypes.UKEIG,
    "Overseas Entity": CompanyTypes.REGISTERED_OVERSEAS_ENTITY,
    "Further Education and Sixth Form College Corps": CompanyTypes.FURTHER_EDUCATION_OR_SIXTH_FORM_COLLEGE_CORPORATION,
    "Other Company Type": CompanyTypes.OTHER,
    "United Kingdom Societas": CompanyTypes.UNITED_KINGDOM_SOCIETAS,
    "Authorised Company Service Provider": CompanyTypes.AUTHORISED_COMPANY_SERVICE_PROVIDER,
}


@dataclass
class CompaniesHouseAccount:
    barcode: str  # 'JDCG3G3A',
    category: str  # 'accounts',
    company_number: str  # '01005861',
    created_at: DateTime  # '2015-01-31T15:33:33.810139814Z',
    date: Date  # '1999-05-10',
    description_values: dict  # {'made_up_date': '1998-08-31'},
    description: str  # 'accounts-with-made-up-date',
    etag: str  # '',
    filename: str  # '',
    links: dict  # {'self': '/company/01005861/filing-history/MTA4NjgyMzZhZGlxemtjeA', 'document_metadata': 'https://frontend-doc-api.company-information.service.gov.uk/document/3B7_XxZYKpZ38k8YBPKTpfLH2ti93ludDM6RfmUFrQA'},
    pages: int  # 16,
    resources: dict  # {'application/pdf': {'content_length': 312727}}
    significant_date_type: str  # '',
    significant_date: DateTime  # '1998-08-31T00:00:00Z',
    transaction_id: str  # 'MTA4NjgyMzZhZGlxemtjeA',
    type: str  # 'AA',
    paper_filed: bool = None  # True,
    action_date: Date = None  # '1998-08-31',

    def __post_init__(self):
        datetime_fields = ["created_at", "significant_date"]
        date_fields = ["date", "action_date"]
        for f in datetime_fields:
            if getattr(self, f, None):
                setattr(
                    self,
                    f,
                    isoparse(getattr(self, f)),
                )
        for f in date_fields:
            if getattr(self, f, None):
                setattr(self, f, Date.fromisoformat(getattr(self, f)))

    def to_json(self):
        values = self.__dict__.copy()
        date_fields = ("created_at", "significant_date", "date", "action_date")
        for f in date_fields:
            if getattr(self, f, None):
                values[f] = getattr(self, f).isoformat()
        return values

    @property
    def accounts_type(self):
        PREFIX = "accounts-with-accounts-type-"
        if self.description.startswith(PREFIX):
            return self.description[len(PREFIX) :]

    @property
    def filetype(self):
        for filetype in FileTypes:
            if filetype.value in self.resources.keys():
                return filetype.value

    @property
    def financial_year_end(self):
        if self.significant_date:
            return self.significant_date
        if self.description_values.get("made_up_date"):
            return Date.fromisoformat(self.description_values.get("made_up_date"))
        return None

    @property
    def has_ixbrl(self):
        return FileTypes.IXBRL.value in self.resources.keys()

    @property
    def has_pdf(self):
        return FileTypes.PDF.value in self.resources.keys()


class CompaniesHouseAPI:
    FILING_HISTORY_URL = "https://api.company-information.service.gov.uk/company/{company_number}/filing-history?category=accounts"
    DOC_METADATA_URL = (
        "https://document-api.company-information.service.gov.uk/document/{document_id}"
    )
    COMPANY_PROFILE_URL = (
        "https://api.company-information.service.gov.uk/company/{company_number}"
    )

    def __init__(self, api_key, session=None):
        self.api_key = api_key
        self.session = session or requests.Session()
        self.session.auth = (self.api_key, "")

    def _fetch_url(self, url):
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_company(self, company_number):
        url = self.COMPANY_PROFILE_URL.format(company_number=company_number)
        return self._fetch_url(url)

    def get_accounts(self, company_number):
        url = self.FILING_HISTORY_URL.format(company_number=company_number)
        result = self._fetch_url(url)
        for item in result["items"]:
            if item["type"] != "AA":
                continue
            if item.get("links", {}).get("document_metadata"):
                q = self.session.get(item["links"]["document_metadata"])
                q.raise_for_status()
                item = CompaniesHouseAccount(
                    **{
                        **item,
                        **q.json(),
                    }
                )
                yield item

    def fetch_account_ixbrl(self, account: CompaniesHouseAccount):
        if account.has_ixbrl:
            ixbrl_url = account.links.get("document")
            if not ixbrl_url:
                raise ValueError("No document available")
            ixbrl_response = self.session.get(
                ixbrl_url, headers={"Accept": "application/xhtml+xml"}
            )
            ixbrl_response.raise_for_status()
            return ixbrl_response.content
        else:
            raise ValueError("No IXBRL document available")
