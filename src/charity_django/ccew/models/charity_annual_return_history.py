from django.db import models

from charity_django.utils.numbers import scale, scale_value, scale_value_format

from .charity import Charity


class CharityAnnualReturnHistory(models.Model):
    date_of_extract = models.DateField(
        null=True,
        blank=True,
        help_text="The date that the extract was taken from the main dataset.",
    )
    charity = models.ForeignKey(
        Charity,
        db_column="organisation_number",
        to_field="organisation_number",
        on_delete=models.DO_NOTHING,
        help_text="The organisation number for the charity. This is the index value for the charity.",
        related_name="annual_return_history",
        db_constraint=False,
    )
    registered_charity_number = models.IntegerField(
        db_index=True,
        help_text="The registration number of the registered organisation allocated by the Commission. Note that a main charity and all its linked charities will share the same registered_charity_number.",
    )
    fin_period_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="The start date of the financial period which is detailed for the charity.",
    )
    fin_period_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="The end date of the financial period which is detailed for the charity.",
    )
    ar_cycle_reference = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The annual return cycle to which the submission details relate.",
    )
    reporting_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="The due date of the financial period which is detailed for the charity.",
    )
    date_annual_return_received = models.DateField(
        null=True,
        blank=True,
        help_text="The date the annual return was received for the financial period which is detailed for the charity.",
    )
    date_accounts_received = models.DateField(
        null=True,
        blank=True,
        help_text="The date the charity accounts were received for the financial period which is detailed for the charity.",
    )
    total_gross_income = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="The total gross income reported on Part A of the annual return for the financial period detailed.",
    )
    total_gross_expenditure = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="The total gross expenditure reported on Part A of the annual return for the financial period detailed.",
    )
    accounts_qualified = models.BooleanField(
        null=True,
        blank=True,
        help_text="Indicates whether the accounts have a qualified opinion. (True or NULL)",
    )
    suppression_ind = models.BooleanField(
        null=True,
        blank=True,
        help_text="An indicator of whether the finances for this year are currently suppressed. 1 = Supressed, 0 = not supressed.",
    )
    suppression_type = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Annual Return History"
        verbose_name_plural = "Annual Return History"
        constraints = [
            models.UniqueConstraint(
                fields=["charity", "fin_period_end_date", "ar_cycle_reference"],
                name="unique_annual_return_history",
            ),
        ]

    @property
    def scale(self):
        return scale([self.total_gross_income, self.total_gross_expenditure])

    def scale_value(self, attr):
        if isinstance(attr, (float, int)):
            value = attr
        else:
            value = getattr(self, attr) or 0
        return scale_value(value, self.scale)

    def scale_value_format(self, attr, with_currency=True, if_zero="-"):
        if isinstance(attr, (float, int)):
            value = attr
        else:
            value = getattr(self, attr) or 0
        return scale_value_format(
            value,
            self.scale,
            with_currency=with_currency,
            if_zero=if_zero,
        )
