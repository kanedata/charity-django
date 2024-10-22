from django.db import models


class ClassificationTypes(models.TextChoices):
    """Classification types"""

    WHAT_THE_CHARITY_DOES = "What the charity does"
    WHO_THE_CHARITY_HELPS = "Who the charity helps"
    HOW_THE_CHARITY_WORKS = "How the charity works"


class Charity(models.Model):
    reg_charity_number = models.IntegerField(
        verbose_name="Reg charity number",
        primary_key=True,
    )
    charity_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Charity name",
    )
    date_registered = models.DateField(
        verbose_name="Date registered", null=True, blank=True
    )
    status = models.CharField(
        max_length=255, verbose_name="Status", null=True, blank=True
    )
    date_for_financial_year_ending = models.DateField(
        verbose_name="Date for financial year ending", null=True, blank=True
    )
    total_income = models.BigIntegerField(
        verbose_name="Total income", null=True, blank=True
    )
    total_spending = models.BigIntegerField(
        verbose_name="Total spending", null=True, blank=True
    )
    charitable_spending = models.BigIntegerField(
        verbose_name="Charitable spending", null=True, blank=True
    )
    income_generation_and_governance = models.BigIntegerField(
        verbose_name="Income generation and governance", null=True, blank=True
    )
    public_address = models.TextField(
        verbose_name="Public address",
        null=True,
        blank=True,
    )
    website = models.URLField(
        verbose_name="Website",
        null=True,
        blank=True,
    )
    email = models.EmailField(
        verbose_name="Email",
        null=True,
        blank=True,
    )
    telephone = models.CharField(
        max_length=255,
        verbose_name="Telephone",
        null=True,
        blank=True,
    )
    company_number = models.CharField(
        max_length=255,
        verbose_name="Company number",
        null=True,
        blank=True,
    )

    charitable_purposes = models.TextField(
        verbose_name="Charitable purposes",
        null=True,
        blank=True,
    )
    other_name = models.CharField(
        max_length=255,
        verbose_name="Other name",
        null=True,
        blank=True,
    )
    type_of_governing_document = models.CharField(
        max_length=255,
        verbose_name="Type of governing document",
        null=True,
        blank=True,
    )
    financial_period_start = models.DateField(
        verbose_name="Financial period start",
        null=True,
        blank=True,
    )
    financial_period_end = models.DateField(
        verbose_name="Financial period end",
        null=True,
        blank=True,
    )
    total_income_previous_financial_period = models.IntegerField(
        verbose_name="Total income. Previous financial period.",
        null=True,
        blank=True,
    )
    employed_staff = models.IntegerField(
        verbose_name="Employed staff",
        null=True,
        blank=True,
    )
    uk_and_ireland_volunteers = models.IntegerField(
        verbose_name="UK and Ireland volunteers",
        null=True,
        blank=True,
    )
    income_from_donations_and_legacies = models.IntegerField(
        verbose_name="Income from donations and legacies",
        null=True,
        blank=True,
    )
    income_from_charitable_activities = models.IntegerField(
        verbose_name="Income from charitable activities",
        null=True,
        blank=True,
    )
    income_from_other_trading_activities = models.IntegerField(
        verbose_name="Income from other trading activities",
        null=True,
        blank=True,
    )
    income_from_investments = models.IntegerField(
        verbose_name="Income from investments",
        null=True,
        blank=True,
    )
    income_from_other = models.IntegerField(
        verbose_name="Income from other",
        null=True,
        blank=True,
    )
    total_income_and_endowments = models.IntegerField(
        verbose_name="Total income and endowments",
        null=True,
        blank=True,
    )
    expenditure_on_raising_funds = models.IntegerField(
        verbose_name="Expenditure on Raising funds",
        null=True,
        blank=True,
    )
    expenditure_on_charitable_activities = models.IntegerField(
        verbose_name="Expenditure on Charitable activities",
        null=True,
        blank=True,
    )
    expenditure_on_governance = models.IntegerField(
        verbose_name="Expenditure on Governance",
        null=True,
        blank=True,
    )
    expenditure_on_other = models.IntegerField(
        verbose_name="Expenditure on Other",
        null=True,
        blank=True,
    )
    total_expenditure = models.IntegerField(
        verbose_name="Total expenditure",
        null=True,
        blank=True,
    )
    assets_and_liabilities_total_fixed_assets = models.IntegerField(
        verbose_name="Assets and liabilities - Total fixed assets",
        null=True,
        blank=True,
    )
    total_net_assets_and_liabilities = models.IntegerField(
        verbose_name="Total net assets and liabilities",
        null=True,
        blank=True,
    )

    @property
    def what_the_charity_does(self):
        return self.classifications.filter(
            classification_type=ClassificationTypes.WHAT_THE_CHARITY_DOES
        ).values_list("classification", flat=True)

    @property
    def who_the_charity_helps(self):
        return self.classifications.filter(
            classification_type=ClassificationTypes.WHO_THE_CHARITY_HELPS
        ).values_list("classification", flat=True)

    @property
    def how_the_charity_works(self):
        return self.classifications.filter(
            classification_type=ClassificationTypes.HOW_THE_CHARITY_WORKS
        ).values_list("classification", flat=True)

    @property
    def org_id(self):
        return f"GB-CHC-{self.reg_charity_number}"

    def __str__(self) -> str:
        return f"{self.charity_name} [{self.reg_charity_number}]"

    class Meta:
        verbose_name = "Charity in Northern Ireland"
        verbose_name_plural = "Charities in Northern Ireland"


class CharityClassification(models.Model):
    charity = models.ForeignKey(
        Charity,
        on_delete=models.CASCADE,
        verbose_name="Charity",
        related_name="classifications",
        db_constraint=False,
    )
    classification_type = models.CharField(
        max_length=255,
        choices=ClassificationTypes.choices,
        verbose_name="Classification type",
    )
    classification = models.CharField(
        max_length=255,
        verbose_name="Classification",
    )

    class Meta:
        verbose_name = "Charity classification"
        verbose_name_plural = "Charity classifications"
        unique_together = (("charity_id", "classification_type", "classification"),)
