from enum import unique
from tabnanny import verbose

from django.db import NotSupportedError, connections, models
from django.db.models.constants import OnConflict

from charity_django.companies.ch_api import (
    COMPANY_CATEGORY_NAME_LOOKUP,
    COMPANY_STATUS_NAME_LOOKUP,
    NONPROFIT_TYPES,
    AccountTypes,
    CompanyStatuses,
    CompanyTypes,
)


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
                    "bulk_create() cannot be used with primary keys in "
                    "update_fields."
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
    CompanyName = models.CharField(max_length=255, db_index=True)
    CompanyNumber = models.CharField(max_length=10, db_index=True, primary_key=True)
    RegAddress_CareOf = models.CharField(max_length=255, null=True, blank=True)
    RegAddress_POBox = models.CharField(max_length=255, null=True, blank=True)
    RegAddress_AddressLine1 = models.CharField(max_length=255, null=True, blank=True)
    RegAddress_AddressLine2 = models.CharField(max_length=255, null=True, blank=True)
    RegAddress_PostTown = models.CharField(max_length=255, null=True, blank=True)
    RegAddress_County = models.CharField(max_length=255, null=True, blank=True)
    RegAddress_Country = models.CharField(max_length=255, null=True, blank=True)
    RegAddress_PostCode = models.CharField(
        max_length=255, db_index=True, null=True, blank=True
    )
    CompanyCategory = models.CharField(
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
        choices=[(x.value, x.name) for x in CompanyTypes],
    )
    CompanyStatus = models.CharField(
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
        choices=[(x.value, x.name) for x in CompanyStatuses],
    )
    CountryOfOrigin = models.CharField(
        max_length=255, db_index=True, null=True, blank=True
    )
    DissolutionDate = models.DateField(db_index=True, null=True, blank=True)
    IncorporationDate = models.DateField(db_index=True, null=True, blank=True)
    Accounts_AccountRefDay = models.IntegerField(null=True, blank=True)
    Accounts_AccountRefMonth = models.IntegerField(null=True, blank=True)
    Accounts_NextDueDate = models.DateField(null=True, blank=True)
    Accounts_LastMadeUpDate = models.DateField(null=True, blank=True)
    Accounts_AccountCategory = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=[(x.value, x.name) for x in AccountTypes],
    )
    Returns_NextDueDate = models.DateField(null=True, blank=True)
    Returns_LastMadeUpDate = models.DateField(null=True, blank=True)
    Mortgages_NumMortCharges = models.IntegerField(null=True, blank=True)
    Mortgages_NumMortOutstanding = models.IntegerField(null=True, blank=True)
    Mortgages_NumMortPartSatisfied = models.IntegerField(null=True, blank=True)
    Mortgages_NumMortSatisfied = models.IntegerField(null=True, blank=True)
    LimitedPartnerships_NumGenPartners = models.IntegerField(null=True, blank=True)
    LimitedPartnerships_NumLimPartners = models.IntegerField(null=True, blank=True)
    ConfStmtNextDueDate = models.DateField(null=True, blank=True)
    ConfStmtLastMadeUpDate = models.DateField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    in_latest_update = models.BooleanField(default=False, db_index=True)

    @property
    def is_nonprofit(self):
        return self.CompanyCategory in NONPROFIT_TYPES

    @property
    def org_id(self):
        return "GB-COH-{}".format(self.CompanyNumber)

    @property
    def status(self):
        return self.get_CompanyStatus_display()

    @property
    def category(self):
        return self.get_CompanyCategory_display()

    def get_CompanyCategory_display(self):
        return COMPANY_CATEGORY_NAME_LOOKUP.get(
            self.CompanyCategory, self.CompanyCategory
        )

    def get_CompanyStatus_display(self):
        return COMPANY_STATUS_NAME_LOOKUP.get(self.CompanyStatus, self.CompanyStatus)

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
        choices=[(x.value, x.name) for x in AccountTypes],
        null=True,
        blank=True,
    )
    objects = CompanyManager()

    class Meta:
        unique_together = [["company", "financial_year_end"]]
