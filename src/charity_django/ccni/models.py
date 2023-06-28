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
    sub_charity_number = models.IntegerField(
        verbose_name="Sub charity number", default=0
    )
    charity_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Charity name",
    )
    date_registered = models.DateField(
        verbose_name="Date registered",
    )
    status = models.CharField(
        max_length=255,
        verbose_name="Status",
    )
    date_for_financial_year_ending = models.DateField(
        verbose_name="Date for financial year ending",
    )
    total_income = models.BigIntegerField(
        verbose_name="Total income",
    )
    total_spending = models.BigIntegerField(
        verbose_name="Total spending",
    )
    charitable_spending = models.BigIntegerField(
        verbose_name="Charitable spending",
    )
    income_generation_and_governance = models.BigIntegerField(
        verbose_name="Income generation and governance",
    )
    retained_for_future_use = models.BigIntegerField(
        verbose_name="Retained for future use",
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
