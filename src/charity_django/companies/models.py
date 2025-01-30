from django.db import NotSupportedError, connections, models
from django.db.models.constants import OnConflict

from charity_django.companies.ch_api import (
    NONPROFIT_TYPES,
    AccountTypes,
    CompanyStatuses,
    CompanyTypes,
)


class CompanyStatusChoices(models.TextChoices):
    ACTIVE = CompanyStatuses.ACTIVE.value, "Active"
    ACTIVE_PROPOSAL_TO_STRIKE_OFF = (
        CompanyStatuses.ACTIVE_PROPOSAL_TO_STRIKE_OFF.value,
        "Active - Proposal to Strike off",
    )
    DISSOLVED = CompanyStatuses.DISSOLVED.value, "Dissolved"
    LIQUIDATION = CompanyStatuses.LIQUIDATION.value, "Liquidation"
    RECEIVERSHIP = CompanyStatuses.RECEIVERSHIP.value, "Receivership"
    ADMINISTRATION = CompanyStatuses.ADMINISTRATION.value, "Administration"
    VOLUNTARY_ARRANGEMENT = (
        CompanyStatuses.VOLUNTARY_ARRANGEMENT.value,
        "Voluntary arrangement",
    )
    CONVERTED_CLOSED = CompanyStatuses.CONVERTED_CLOSED.value, "Converted/Closed"
    INSOLVENCY_PROCEEDINGS = (
        CompanyStatuses.INSOLVENCY_PROCEEDINGS.value,
        "Insolvency proceedings",
    )
    REGISTERED = CompanyStatuses.REGISTERED.value, "Registered"
    REMOVED = CompanyStatuses.REMOVED.value, "Removed"
    CLOSED = CompanyStatuses.CLOSED.value, "Closed"
    OPEN = CompanyStatuses.OPEN.value, "Open"


class CompanyTypeChoices(models.TextChoices):
    ASSURANCE_COMPANY = CompanyTypes.ASSURANCE_COMPANY.value, "Assurance company"
    CHARITABLE_INCORPORATED_ORGANISATION = (
        CompanyTypes.CHARITABLE_INCORPORATED_ORGANISATION.value,
        "Charitable Incorporated Organisation",
    )
    COMMUNITY_INTEREST_COMPANY = (
        CompanyTypes.COMMUNITY_INTEREST_COMPANY.value,
        "Community Interest Company",
    )
    CONVERTED_OR_CLOSED = CompanyTypes.CONVERTED_OR_CLOSED.value, "Converted/Closed"
    EEIG = CompanyTypes.EEIG.value, "European Economic Interest Grouping (EEIG)"
    EEIG_ESTABLISHMENT = CompanyTypes.EEIG_ESTABLISHMENT.value, "EEIG Establishment"
    EUROPEAN_PUBLIC_LIMITED_LIABILITY_COMPANY_SE = (
        CompanyTypes.EUROPEAN_PUBLIC_LIMITED_LIABILITY_COMPANY_SE.value,
        "European Public Limited-Liability Company (SE)",
    )
    FURTHER_EDUCATION_OR_SIXTH_FORM_COLLEGE_CORPORATION = (
        CompanyTypes.FURTHER_EDUCATION_OR_SIXTH_FORM_COLLEGE_CORPORATION.value,
        "Further education or sixth form college corporation",
    )
    ICVC_SECURITIES = (
        CompanyTypes.ICVC_SECURITIES.value,
        "Investment Company with Variable Capital (Securities)",
    )
    ICVC_UMBRELLA = (
        CompanyTypes.ICVC_UMBRELLA.value,
        "Investment Company with Variable Capital (Umbrella)",
    )
    ICVC_WARRANT = (
        CompanyTypes.ICVC_WARRANT.value,
        "Investment Company with Variable Capital (Warrant)",
    )
    INDUSTRIAL_AND_PROVIDENT_SOCIETY = (
        CompanyTypes.INDUSTRIAL_AND_PROVIDENT_SOCIETY.value,
        "Industrial and Provident Society",
    )
    INVESTMENT_COMPANY_WITH_VARIABLE_CAPITAL = (
        CompanyTypes.INVESTMENT_COMPANY_WITH_VARIABLE_CAPITAL.value,
        "Investment Company with Variable Capital",
    )
    LIMITED_PARTNERSHIP = CompanyTypes.LIMITED_PARTNERSHIP.value, "Limited Partnership"
    LLP = CompanyTypes.LLP.value, "Limited Liability Partnership"
    LTD = CompanyTypes.LTD.value, "Private Limited Company"
    NORTHERN_IRELAND = CompanyTypes.NORTHERN_IRELAND.value, "Northern Ireland"
    NORTHERN_IRELAND_OTHER = (
        CompanyTypes.NORTHERN_IRELAND_OTHER.value,
        "Northern Ireland Other",
    )
    OLD_PUBLIC_COMPANY = CompanyTypes.OLD_PUBLIC_COMPANY.value, "Old Public Company"
    OTHER = CompanyTypes.OTHER.value, "Other company type"
    OVERSEA_COMPANY = CompanyTypes.OVERSEA_COMPANY.value, "Overseas company"
    PLC = CompanyTypes.PLC.value, "Public Limited Company"
    PRIVATE_FUND_LIMITED_PARTNERSHIP = (
        CompanyTypes.PRIVATE_FUND_LIMITED_PARTNERSHIP.value,
        "Private Fund Limited Partnership (PFLP)",
    )
    PRIVATE_LIMITED_GUARANT_NSC_LIMITED_EXEMPTION = (
        CompanyTypes.PRIVATE_LIMITED_GUARANT_NSC_LIMITED_EXEMPTION.value,
        "Company Limited by Guarantee (no share capital, use of 'Limited' exemption)",
    )
    PRIVATE_LIMITED_GUARANT_NSC = (
        CompanyTypes.PRIVATE_LIMITED_GUARANT_NSC.value,
        "Company Limited by Guarantee (no share capital)",
    )
    PRIVATE_LIMITED_SHARES_SECTION_30_EXEMPTION = (
        CompanyTypes.PRIVATE_LIMITED_SHARES_SECTION_30_EXEMPTION.value,
        "Private limited company (section 30 of the Companies Act)",
    )
    PRIVATE_UNLIMITED_NSC = (
        CompanyTypes.PRIVATE_UNLIMITED_NSC.value,
        "Private Unlimited Company (No Share Capital)",
    )
    PRIVATE_UNLIMITED = (
        CompanyTypes.PRIVATE_UNLIMITED.value,
        "Private Unlimited Company",
    )
    PROTECTED_CELL_COMPANY = (
        CompanyTypes.PROTECTED_CELL_COMPANY.value,
        "Protected Cell Company",
    )
    REGISTERED_OVERSEAS_ENTITY = (
        CompanyTypes.REGISTERED_OVERSEAS_ENTITY.value,
        "Registered Overseas Entity",
    )
    REGISTERED_SOCIETY_NON_JURISDICTIONAL = (
        CompanyTypes.REGISTERED_SOCIETY_NON_JURISDICTIONAL.value,
        "Registered Society",
    )
    ROYAL_CHARTER = CompanyTypes.ROYAL_CHARTER.value, "Royal Charter Company"
    SCOTTISH_CHARITABLE_INCORPORATED_ORGANISATION = (
        CompanyTypes.SCOTTISH_CHARITABLE_INCORPORATED_ORGANISATION.value,
        "Scottish Charitable Incorporated Organisation",
    )
    SCOTTISH_PARTNERSHIP = (
        CompanyTypes.SCOTTISH_PARTNERSHIP.value,
        "Scottish Partnership",
    )
    UK_ESTABLISHMENT = (
        CompanyTypes.UK_ESTABLISHMENT.value,
        "United Kingdom Establishment",
    )
    UKEIG = CompanyTypes.UKEIG.value, "United Kingdom Economic Interest Grouping"
    UNITED_KINGDOM_SOCIETAS = (
        CompanyTypes.UNITED_KINGDOM_SOCIETAS.value,
        "United Kingdom Societas",
    )
    UNREGISTERED_COMPANY = (
        CompanyTypes.UNREGISTERED_COMPANY.value,
        "Unregistered Company",
    )


class AccountTypeChoices(models.TextChoices):
    NULL = AccountTypes.NULL.value, "Null"
    FULL = AccountTypes.FULL.value, "Full"
    SMALL = AccountTypes.SMALL.value, "Small"
    MEDIUM = AccountTypes.MEDIUM.value, "Medium"
    GROUP = AccountTypes.GROUP.value, "Group"
    DORMANT = AccountTypes.DORMANT.value, "Dormant"
    INTERIM = AccountTypes.INTERIM.value, "Interim"
    INITIAL = AccountTypes.INITIAL.value, "Initial"
    TOTAL_EXEMPTION_FULL = (
        AccountTypes.TOTAL_EXEMPTION_FULL.value,
        "Total Exemption Full",
    )
    TOTAL_EXEMPTION_SMALL = (
        AccountTypes.TOTAL_EXEMPTION_SMALL.value,
        "Total Exemption Small",
    )
    PARTIAL_EXEMPTION = AccountTypes.PARTIAL_EXEMPTION.value, "Partial Exemption"
    AUDIT_EXEMPTION_SUBSIDIARY = (
        AccountTypes.AUDIT_EXEMPTION_SUBSIDIARY.value,
        "Audit Exemption Subsidiary",
    )
    FILING_EXEMPTION_SUBSIDIARY = (
        AccountTypes.FILING_EXEMPTION_SUBSIDIARY.value,
        "Filing Exemption Subsidiary",
    )
    MICRO_ENTITY = AccountTypes.MICRO_ENTITY.value, "Micro Entity"
    NO_ACCOUNTS_TYPE_AVAILABLE = (
        AccountTypes.NO_ACCOUNTS_TYPE_AVAILABLE.value,
        "No accounts type available",
    )
    AUDITED_ABRIDGED = AccountTypes.AUDITED_ABRIDGED.value, "Audited abridged"
    UNAUDITED_ABRIDGED = AccountTypes.UNAUDITED_ABRIDGED.value, "Unaudited abridged"
    NO_ACCOUNTS_FILED = AccountTypes.NO_ACCOUNTS_FILED.value, "Unaudited abridged"


class CompanyQuerySet(models.query.QuerySet):
    def _check_bulk_create_options(
        self, ignore_conflicts, update_conflicts, update_fields, unique_fields
    ):
        if ignore_conflicts and update_conflicts:
            raise ValueError(
                "ignore_conflicts and update_conflicts are mutually exclusive."
            )
        db_features = connections[self.db].features
        if ignore_conflicts:
            if not db_features.supports_ignore_conflicts:
                raise NotSupportedError(
                    "This database backend does not support ignoring conflicts."
                )
            return OnConflict.IGNORE
        elif update_conflicts:
            if not db_features.supports_update_conflicts:
                raise NotSupportedError(
                    "This database backend does not support updating conflicts."
                )
            if not update_fields:
                raise ValueError(
                    "Fields that will be updated when a row insertion fails "
                    "on conflicts must be provided."
                )
            if unique_fields and not db_features.supports_update_conflicts_with_target:
                raise NotSupportedError(
                    "This database backend does not support updating "
                    "conflicts with specifying unique fields that can trigger "
                    "the upsert."
                )
            if not unique_fields and db_features.supports_update_conflicts_with_target:
                raise ValueError(
                    "Unique fields that can trigger the upsert must be provided."
                )
            # Updating primary keys and non-concrete fields is forbidden.
            update_fields = [
                self.model._meta.get_field(name) if isinstance(name, str) else name
                for name in update_fields
                if name
            ]
            if any(not f.concrete or f.many_to_many for f in update_fields):
                raise ValueError(
                    "bulk_create() can only be used with concrete fields in "
                    "update_fields."
                )
            if any(f.primary_key for f in update_fields):
                raise ValueError(
                    "bulk_create() cannot be used with primary keys in update_fields."
                )
            if unique_fields:
                available_fields = {
                    f.get_attname_column()[1]: f for f in self.model._meta.get_fields()
                }
                # Primary key is allowed in unique_fields.
                unique_fields = [
                    available_fields.get(
                        name if isinstance(name, str) else (name.db_column or name.name)
                    )
                    for name in unique_fields
                    if name != "pk"
                ]
                if any(not f.concrete or f.many_to_many for f in unique_fields):
                    raise ValueError(
                        "bulk_create() can only be used with concrete fields "
                        "in unique_fields."
                    )
            return OnConflict.UPDATE
        return None


class CompanyManager(models.Manager):
    def get_queryset(self):
        return CompanyQuerySet(self.model)


class Company(models.Model):
    CompanyName = models.CharField(
        max_length=255, db_index=True, verbose_name="Company Name"
    )
    CompanyNumber = models.CharField(
        max_length=10, db_index=True, primary_key=True, verbose_name="Company Number"
    )
    RegAddress_CareOf = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Care Of"
    )
    RegAddress_POBox = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="PO Box"
    )
    RegAddress_AddressLine1 = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Address Line 1"
    )
    RegAddress_AddressLine2 = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Address Line 2"
    )
    RegAddress_PostTown = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Post Town"
    )
    RegAddress_County = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="County"
    )
    RegAddress_Country = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Country"
    )
    RegAddress_PostCode = models.CharField(
        max_length=255, db_index=True, null=True, blank=True, verbose_name="Post Code"
    )
    CompanyCategory = models.CharField(
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
        choices=CompanyTypeChoices.choices,
        verbose_name="Type",
    )
    CompanyStatus = models.CharField(
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
        choices=CompanyStatusChoices.choices,
        verbose_name="Status",
    )
    CountryOfOrigin = models.CharField(
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
        verbose_name="Country of Origin",
    )
    DissolutionDate = models.DateField(
        db_index=True, null=True, blank=True, verbose_name="Dissolution Date"
    )
    IncorporationDate = models.DateField(
        db_index=True, null=True, blank=True, verbose_name="Incorporation Date"
    )
    Accounts_AccountRefDay = models.IntegerField(
        null=True, blank=True, verbose_name="Account Reference Day"
    )
    Accounts_AccountRefMonth = models.IntegerField(
        null=True, blank=True, verbose_name="Account Reference Month"
    )
    Accounts_NextDueDate = models.DateField(
        null=True, blank=True, verbose_name="Accounts next due"
    )
    Accounts_LastMadeUpDate = models.DateField(
        null=True, blank=True, verbose_name="Accounts last made up"
    )
    Accounts_AccountCategory = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=AccountTypeChoices.choices,
        verbose_name="Account Category",
    )
    Returns_NextDueDate = models.DateField(
        null=True, blank=True, verbose_name="Returns next due"
    )
    Returns_LastMadeUpDate = models.DateField(
        null=True, blank=True, verbose_name="Returns last made up"
    )
    Mortgages_NumMortCharges = models.IntegerField(
        null=True, blank=True, verbose_name="Mortgage charges"
    )
    Mortgages_NumMortOutstanding = models.IntegerField(
        null=True, blank=True, verbose_name="Outstanding mortgages"
    )
    Mortgages_NumMortPartSatisfied = models.IntegerField(
        null=True, blank=True, verbose_name="Partially satisfied mortgages"
    )
    Mortgages_NumMortSatisfied = models.IntegerField(
        null=True, blank=True, verbose_name="Satisfied mortgages"
    )
    LimitedPartnerships_NumGenPartners = models.IntegerField(
        null=True, blank=True, verbose_name="General partners"
    )
    LimitedPartnerships_NumLimPartners = models.IntegerField(
        null=True, blank=True, verbose_name="Limited partners"
    )
    ConfStmtNextDueDate = models.DateField(
        null=True, blank=True, verbose_name="Confirmation statement next due"
    )
    ConfStmtLastMadeUpDate = models.DateField(
        null=True, blank=True, verbose_name="Confirmation statement last made up"
    )
    last_updated = models.DateTimeField(auto_now=True)
    in_latest_update = models.BooleanField(default=False, db_index=True)

    @property
    def is_nonprofit(self):
        return self.CompanyCategory in [n.value for n in NONPROFIT_TYPES]

    @property
    def org_id(self):
        return "GB-COH-{}".format(self.CompanyNumber)

    def __str__(self):
        return "<Company {} [{}]>".format(self.CompanyName, self.CompanyNumber)

    class Meta:
        verbose_name_plural = "Companies"


class SICCode(models.Model):
    code = models.CharField(max_length=255, db_index=True, primary_key=True)
    title = models.CharField(max_length=255, db_index=True)

    class Meta:
        verbose_name = "SIC Code"
        verbose_name_plural = "SIC Codes"

    def __str__(self):
        return "{} [{}]".format(self.title, self.code)


class CompanySICCode(models.Model):
    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="sic_codes",
        db_column="CompanyNumber",
        db_constraint=False,
    )
    sic_code = models.ForeignKey(
        "SICCode",
        on_delete=models.CASCADE,
        related_name="companies",
        db_column="code",
        db_constraint=False,
    )
    in_latest_update = models.BooleanField(default=False, db_index=True)

    objects = CompanyManager()

    class Meta:
        unique_together = [("company", "sic_code")]


class PreviousName(models.Model):
    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="previous_names",
        db_column="CompanyNumber",
        db_constraint=False,
    )
    ConDate = models.DateField(null=True, blank=True)
    CompanyName = models.CharField(max_length=255)
    in_latest_update = models.BooleanField(default=False, db_index=True)
    objects = CompanyManager()

    def __str__(self):
        return "<Previous name {} for {}>".format(
            self.CompanyName, self.company.CompanyName
        )

    class Meta:
        unique_together = [("company", "CompanyName")]


class Account(models.Model):
    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="accounts",
        db_column="CompanyNumber",
        db_constraint=False,
    )
    financial_year_end = models.DateField(db_index=True)
    category = models.CharField(
        max_length=255,
        db_index=True,
        choices=AccountTypeChoices.choices,
        null=True,
        blank=True,
    )
    objects = CompanyManager()

    class Meta:
        unique_together = [["company", "financial_year_end"]]
