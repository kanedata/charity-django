from django.db import models

# Report Activity
# Beneficiaries


class ClassificationTypes(models.TextChoices):
    """Classification types"""

    CHARITY_CLASSIFICATION = "Charity Classification"
    CHARITABLE_PURPOSE = "Charitable Purpose"
    REPORT_ACTIVITY = "Report Activity"
    BENEFICIARIES = "Beneficiaries"
    OPERATES_IN = "Operates In"


class CharityStatus(models.TextChoices):
    """Charity status types"""

    REGISTERED = "Registered"
    DEREGISTERED = "Deregistered"
    DEREGISTERED_S40 = "Deregistered S40 by Revenue"


class FinancialBand(models.IntegerChoices):
    """Financial bands"""

    UNDER_250K = 1, "< €250k"
    BETWEEN_250K_AND_500K = 2, "€250k - €500k"
    BETWEEN_501K_AND_2M = 3, "€501k - €2m"
    OVER_2M = 4, "> €2m"


class EmployeeBand(models.IntegerChoices):
    """Employee bands"""

    BAND_0 = 0, "None"
    BAND_1_9 = 1, "1-9"
    BAND_10_19 = 2, "10-19"
    BAND_20_49 = 3, "20-49"
    BAND_50_249 = 4, "50-249"
    BAND_250_PLUS = 5, "250+"


class VolunteerBand(models.IntegerChoices):
    """Volunteer bands"""

    BAND_0 = 0, "None"
    BAND_1_9 = 1, "1-9"
    BAND_10_19 = 2, "10-19"
    BAND_20_49 = 3, "20-49"
    BAND_50_249 = 4, "50-249"
    BAND_250_499 = 5, "250-499"
    BAND_500_999 = 6, "500-999"
    BAND_1000_4999 = 7, "1000-4999"
    BAND_5000_PLUS = 8, "5000+"


class CharityGoverningForm(models.TextChoices):
    ASSOCIATION = "Association"
    BOARD_MANAGEMENT_POST_PRIMARY = "Board Of Management (Post-Primary School)"
    BOARD_MANAGEMENT_PRIMARY = "Board of Management (Primary School)"
    CLG = "CLG - Company Limited by Guarantee"
    CLG_LICENCED = "CLG - Company Limited by Guarantee (licenced company)"
    # CLG2 = "Company Limited by Guarantee"
    CO_OPERATIVE = "Co-operative"
    COMPANY = "Company"
    DAC_SHARES = "DAC - Designated Activity Company (limited by shares)"
    DAC_GUARANTEE_LICENCE = (
        "DAC - Designated Activity Company (guarantee licence company)"
    )
    DAC_LICENCED = (
        "DAC - Designated Activity Company Limited by Shares (licenced company)"
    )
    DAC = "Designated Activity Company"
    EDUCATION_BODY = "Education Body (as defined in the Charities Act 2009)"
    EDUCATIONAL_ENDOWMENT = "Educational Endowment Scheme"
    FOREIGN_REGISTERED = "Foreign Registered Company"
    FRIENDLY_SOCIETY = "Friendly Society"
    HIGH_COURT_SCHEME = "High Court Scheme"
    LTD = "LTD - Private Company Limited by Shares"
    # PRIVATE_LIMITED_COMPANY = "Private Limited Company"
    OTHER = "Other"
    OTHER_TRUST = "Other Trust"
    PRIVATE_CHARITABLE_TRUST = "Private Charitable Trust"
    PRIVATE_UNLIMITED_COMPANY = "Private Unlimited Company"
    # ULC = "ULC - Private Unlimited Company"
    PUBLIC_LIMITED_COMPANY = "Public limited company"
    PULC = "PULC - Public Unlimited Company without share capital"
    ROYAL_CHARTER = "Royal Charter Governance"
    STATUTE = "Statute / Statutory Instrument"
    TRUST = "Trust"


COMPANY_FORM_LOOKUP = {
    "Company Limited by Guarantee": CharityGoverningForm.CLG,
    "Private Limited Company": CharityGoverningForm.LTD,
    "ULC - Private Unlimited Company": CharityGoverningForm.PRIVATE_UNLIMITED_COMPANY,
    **{f.value: f for f in CharityGoverningForm},
}


class CharityClassificationCategory(models.Model):
    classification_type = models.CharField(
        max_length=255,
        choices=ClassificationTypes.choices,
        verbose_name="Classification type",
    )
    classification_en = models.CharField(
        max_length=255,
        verbose_name="Classification",
        null=True,
        blank=True,
    )
    classification_ga = models.CharField(
        max_length=255,
        verbose_name="Classification",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Charity classification"
        verbose_name_plural = "Charity classifications"
        constraints = [
            models.UniqueConstraint(
                fields=["classification_type", "classification_en"],
                name="unique_classification_type_en",
            ),
            models.UniqueConstraint(
                fields=["classification_type", "classification_ga"],
                name="unique_classification_type_ga",
            ),
        ]


class Charity(models.Model):
    registered_charity_number = models.IntegerField(
        verbose_name="Registered Charity Number",
        primary_key=True,
    )
    registered_charity_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Registered Charity Name",
    )
    status = models.CharField(
        max_length=255,
        verbose_name="Status",
        null=True,
        blank=True,
        choices=CharityStatus.choices,
    )
    primary_address = models.TextField(
        verbose_name="Primary Address",
        null=True,
        blank=True,
    )
    governing_form = models.CharField(
        max_length=255,
        verbose_name="Governing Form",
        null=True,
        blank=True,
        choices=CharityGoverningForm.choices,
    )
    cro_number = models.CharField(
        max_length=255,
        verbose_name="Company Number",
        null=True,
        blank=True,
    )
    country_established = models.CharField(
        max_length=255,
        verbose_name="Country Established",
        null=True,
        blank=True,
    )
    charitable_objects = models.TextField(
        verbose_name="Charitable Objects",
        null=True,
        blank=True,
    )
    charitable_objects_ga = models.TextField(
        verbose_name="Charitable Objects (Irish)",
        null=True,
        blank=True,
    )
    latest_financial_year_end = models.DateField(
        verbose_name="Latest Financial Year End",
        null=True,
        blank=True,
        db_index=True,
    )
    latest_income = models.IntegerField(
        verbose_name="Latest Income",
        null=True,
        blank=True,
        db_index=True,
    )
    latest_expenditure = models.IntegerField(
        verbose_name="Latest Expenditure",
        null=True,
        blank=True,
        db_index=True,
    )
    latest_activity_description = models.TextField(
        verbose_name="Latest Activity Description",
        null=True,
        blank=True,
    )
    latest_activity_description_ga = models.TextField(
        verbose_name="Latest Activity Description (Irish)",
        null=True,
        blank=True,
    )

    classifications = models.ManyToManyField(
        "CharityClassificationCategory",
        verbose_name="Classifications",
        related_name="charities",
        blank=True,
        db_constraint=False,
    )

    @property
    def org_id(self):
        return f"IE-CHY-{self.registered_charity_number}"

    def __str__(self) -> str:
        return f"{self.registered_charity_name} [{self.registered_charity_number}]"

    class Meta:
        verbose_name = "Charity in Ireland"
        verbose_name_plural = "Charities in Ireland"


class CharityName(models.Model):
    charity = models.ForeignKey(
        Charity,
        on_delete=models.CASCADE,
        verbose_name="Charity",
        related_name="names",
        db_constraint=False,
    )
    language = models.CharField(
        max_length=10,
        default="en",
        verbose_name="Language",
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Name",
    )


class CharityFinancialYear(models.Model):
    charity = models.ForeignKey(
        Charity,
        on_delete=models.CASCADE,
        verbose_name="Charity",
        related_name="financial_years",
        db_constraint=False,
    )
    period_start_date = models.DateField(
        verbose_name="Period Start Date",
        null=True,
        blank=True,
    )
    period_end_date = models.DateField(
        verbose_name="Period End Date",
        db_index=True,
    )
    activity_description = models.TextField(
        verbose_name="Activity Description",
        null=True,
        blank=True,
    )
    activity_description_ga = models.TextField(
        verbose_name="Activity Description (Irish)",
        null=True,
        blank=True,
    )
    income_government_or_local_authorities = models.IntegerField(
        verbose_name="Income: Government or Local Authorities",
        null=True,
        blank=True,
    )
    income_other_public_bodies = models.IntegerField(
        verbose_name="Income: Other Public Bodies",
        null=True,
        blank=True,
    )
    income_philantrophic_organisations = models.IntegerField(
        verbose_name="Income: Philantrophic Organisations",
        null=True,
        blank=True,
    )
    income_donations = models.IntegerField(
        verbose_name="Income: Donations",
        null=True,
        blank=True,
    )
    income_trading_and_commercial_activities = models.IntegerField(
        verbose_name="Income: Trading and Commercial Activities",
        null=True,
        blank=True,
    )
    income_other_sources = models.IntegerField(
        verbose_name="Income: Other Sources",
        null=True,
        blank=True,
    )
    income_bequests = models.IntegerField(
        verbose_name="Income: Bequests",
        null=True,
        blank=True,
    )
    gross_income = models.IntegerField(
        verbose_name="Gross Income",
        null=True,
        blank=True,
    )
    gross_expenditure = models.IntegerField(
        verbose_name="Gross Expenditure",
        null=True,
        blank=True,
    )
    surplus_deficit_for_the_period = models.IntegerField(
        verbose_name="Surplus / (Deficit) for the Period",
        null=True,
        blank=True,
    )
    cash_at_hand_and_in_bank = models.IntegerField(
        verbose_name="Cash at Hand and in Bank",
        null=True,
        blank=True,
    )
    other_assets = models.IntegerField(
        verbose_name="Other Assets",
        null=True,
        blank=True,
    )
    total_assets = models.IntegerField(
        verbose_name="Total Assets",
        null=True,
        blank=True,
    )
    total_liabilities = models.IntegerField(
        verbose_name="Total Liabilities",
        null=True,
        blank=True,
    )
    net_assets_liabilities = models.IntegerField(
        verbose_name="Net Assets / (Liabilities)",
        null=True,
        blank=True,
    )
    gross_income_schools = models.CharField(
        max_length=255,
        verbose_name="Gross Income (Schools)",
        null=True,
        blank=True,
        choices=FinancialBand.choices,
    )
    gross_expenditure_schools = models.CharField(
        max_length=255,
        verbose_name="Gross Expenditure (Schools)",
        null=True,
        blank=True,
        choices=FinancialBand.choices,
    )
    number_of_employees = models.CharField(
        max_length=255,
        verbose_name="Number of Employees",
        null=True,
        blank=True,
        choices=EmployeeBand.choices,
    )
    number_of_full_time_employees = models.IntegerField(
        verbose_name="Number of Full-Time Employees",
        null=True,
        blank=True,
    )
    number_of_part_time_employees = models.IntegerField(
        verbose_name="Number of Part-Time Employees",
        null=True,
        blank=True,
    )
    number_of_volunteers = models.CharField(
        max_length=255,
        verbose_name="Number of Volunteers",
        null=True,
        blank=True,
        choices=VolunteerBand.choices,
    )

    classifications = models.ManyToManyField(
        "CharityClassificationCategory",
        verbose_name="Classifications",
        related_name="charity_financial_years",
        blank=True,
        db_constraint=False,
    )

    class Meta:
        verbose_name = "Charity Financial Year"
        verbose_name_plural = "Charity Financial Years"
        constraints = [
            models.UniqueConstraint(
                fields=["charity", "period_end_date"],
                name="unique_charity_financial_year",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.charity.registered_charity_name} [{self.charity.registered_charity_number}] - FY ended {self.period_end_date}"
