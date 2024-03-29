from django.db import models

from charity_django.utils.text import to_titlecase

from .choices import (
    CharityIsCDFOrCIF,
    CharityRegistrationStatus,
    CharityReportingStatus,
    CharityType,
    ClassificationType,
    IndividualOrOrganisation,
)


class Charity(models.Model):
    date_of_extract = models.DateField(
        null=True,
        blank=True,
        help_text="The date that the extract was taken from the main dataset.",
    )
    organisation_number = models.IntegerField(
        db_index=True,
        unique=True,
        help_text="The organisation number for the charity. This is the index value for the charity.",
    )
    registered_charity_number = models.IntegerField(
        db_index=True,
        help_text="The registration number of the registered organisation allocated by the Commission. Note that a main charity and all its linked charities will share the same registered_charity_number.",
    )
    linked_charity_number = models.IntegerField(
        db_index=True,
        help_text="A number that uniquely identifies the subsidiary or group member associated with a registered charity. Used for user identification purposes where the subsidiary is known by the parent registration number and the subsidiary number. The main parent charity has a linked_charity_number of 0.",
    )
    charity_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="The Main Name of the Charity",
    )
    charity_type = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        choices=CharityType.choices,
        help_text="The type of the charity displayed on the public register of charities. Only the main parent charity will have a value for this field (i.e. linked_charity_number=0).",
    )
    charity_registration_status = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        choices=CharityRegistrationStatus.choices,
        help_text="The charity registration status indicates whether a charity is registered or removed",
    )
    date_of_registration = models.DateField(
        null=True,
        blank=True,
        help_text="The date the charity was registered with the Charity Commission.",
    )
    date_of_removal = models.DateField(
        null=True,
        blank=True,
        help_text="This is the date the charity was removed from the Register of Charities. This will not necessarily be the same date that the charity ceased to exist or ceased to operate. For non-removed charities the field is NULL.",
    )
    charity_reporting_status = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=CharityReportingStatus.choices,
        help_text="The current reporting status of the charity",
    )
    latest_acc_fin_period_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="The start date of the latest financial period for which the charity has made a submission.",
    )
    latest_acc_fin_period_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="The end date of the latest financial period for which the charity has made a submission.",
    )
    latest_income = models.FloatField(
        null=True,
        blank=True,
        db_index=True,
        help_text="The latest income submitted by the charity. This is the total gross income submitted on part A of the annual return submission.",
    )
    latest_expenditure = models.FloatField(
        null=True,
        blank=True,
        help_text="The latest expenditure submitted by a charity. This is the expenditure submitted on part A of the annual return submission.",
    )
    charity_contact_address1 = models.CharField(
        max_length=255, null=True, blank=True, help_text="Charity Address Line 1"
    )
    charity_contact_address2 = models.CharField(
        max_length=255, null=True, blank=True, help_text="Charity Address Line 2"
    )
    charity_contact_address3 = models.CharField(
        max_length=255, null=True, blank=True, help_text="Charity Address Line 3"
    )
    charity_contact_address4 = models.CharField(
        max_length=255, null=True, blank=True, help_text="Charity Address Line 4"
    )
    charity_contact_address5 = models.CharField(
        max_length=255, null=True, blank=True, help_text="Charity Address Line 5"
    )
    charity_contact_postcode = models.CharField(
        max_length=255, null=True, blank=True, help_text="Charity Postcode"
    )
    charity_contact_phone = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Charity Public Telephone Number",
    )
    charity_contact_email = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Charity Public email address",
    )
    charity_contact_web = models.CharField(
        max_length=255, null=True, blank=True, help_text="Charity Website Address"
    )
    charity_company_registration_number = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Registered Company Number of the Charity as assigned by Companies House. Integer returned as string",
    )
    charity_insolvent = models.BooleanField(
        null=True, blank=True, help_text="Indicates if the charity is insolvent."
    )
    charity_in_administration = models.BooleanField(
        null=True,
        blank=True,
        help_text="Indicates if the charity is in administration.",
    )
    charity_previously_excepted = models.BooleanField(
        null=True,
        blank=True,
        help_text="Indicates the charity was previously an excepted charity.",
    )
    charity_is_cdf_or_cif = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=CharityIsCDFOrCIF.choices,
        help_text="Indicates whether the charity is a Common Investment Fund or Common Deposit Fund.",
    )
    charity_is_cio = models.BooleanField(
        null=True,
        blank=True,
        help_text="Indicates whether the charity is a Charitable Incorporated Organisation.",
    )
    cio_is_dissolved = models.BooleanField(
        null=True, blank=True, help_text="Indicates the CIO is to be dissolved."
    )
    date_cio_dissolution_notice = models.DateField(
        null=True, blank=True, help_text="Date the CIO dissolution notice expires"
    )
    charity_activities = models.TextField(
        null=True,
        blank=True,
        help_text="The charity activities, the trustees’ description of what they do and who they help.",
    )
    charity_gift_aid = models.BooleanField(
        null=True,
        blank=True,
        help_text="Indicates whether the charity is registered for gift aid with HMRC. True, False, NULL (not known)",
    )
    charity_has_land = models.BooleanField(
        null=True,
        blank=True,
        help_text="Indicates whether the charity owns or leases any land or buildings. True, False, NULL (not known)",
    )

    def __str__(self):
        """Return a string representation of the model"""
        return "{} [{}{}]".format(
            to_titlecase(self.charity_name),
            self.registered_charity_number,
            "-{}".format(self.linked_charity_number)
            if self.linked_charity_number
            else "",
        )

    @property
    def name(self):
        return to_titlecase(self.charity_name)

    @property
    def org_id(self):
        return "GB-CHC-{}".format(self.registered_charity_number)

    @property
    def ccew_url(self):
        return "https://register-of-charities.charitycommission.gov.uk/charity-search/-/charity-details/{}".format(
            self.registered_charity_number
        )

    @property
    def aoo(self):
        result = {
            "uk": [],
            "overseas": [],
        }
        for area in self.area_of_operation.all():
            if area.geographic_area_type in ("Country", "Continent"):
                if area.geographic_area_description in ("Scotland", "Northern Ireland"):
                    result["uk"].append(area)
                else:
                    result["overseas"].append(area)
            else:
                result["uk"].append(area)
        return result

    @property
    def latest_financials(self):
        return self.financials()

    @property
    def chair(self):
        return self.trustees.filter(trustee_is_chair=True).first()

    @property
    def trustees_organisations(self):
        return self.trustees.filter(
            individual_or_organisation=IndividualOrOrganisation.ORGANISATION
        )

    @property
    def trustees_individuals(self):
        return self.trustees.filter(
            individual_or_organisation=IndividualOrOrganisation.INDIVIDUAL
        )

    @property
    def org_ids(self):
        return f"GB-CHC-{self.registered_charity_number}"

    @property
    def what(self):
        return self.classification.filter(
            classification_type=ClassificationType.WHAT
        ).values_list("classification_description", flat=True)

    @property
    def who(self):
        return self.classification.filter(
            classification_type=ClassificationType.WHO
        ).values_list("classification_description", flat=True)

    @property
    def how(self):
        return self.classification.filter(
            classification_type=ClassificationType.HOW
        ).values_list("classification_description", flat=True)

    @property
    def governing_document_description(self):
        gd = self.governing_document.first()
        if gd:
            return gd.governing_document_description

    @property
    def charitable_objects(self):
        gd = self.governing_document.first()
        if gd:
            return gd.charitable_objects

    @property
    def area_of_benefit(self):
        gd = self.governing_document.first()
        if gd:
            return gd.area_of_benefit

    def address(self, join=None):
        address_fields = [
            self.charity_contact_address1,
            self.charity_contact_address2,
            self.charity_contact_address3,
            self.charity_contact_address4,
            self.charity_contact_address5,
            self.charity_contact_postcode,
        ]
        address_fields = [a for a in address_fields if a]
        if isinstance(join, str):
            return join.join(address_fields)
        return address_fields

    def financials(self, on_date=None, exclude_null=True):
        if on_date:
            finances_ar = self.annual_return_history.filter(
                fin_period_end_date__gte=on_date,
                fin_period_start_date__lte=on_date,
            ).first()
        elif exclude_null:
            finances_ar = (
                self.annual_return_history.exclude(total_gross_income__isnull=True)
                .order_by("-fin_period_end_date")
                .first()
            )
        else:
            finances_ar = self.annual_return_history.order_by(
                "-fin_period_end_date"
            ).first()
        finances_parta = (
            self.annual_return_part_a.filter(
                fin_period_end_date=finances_ar.fin_period_end_date
            ).first()
            if finances_ar
            else None
        )
        finances_partb = (
            self.annual_return_part_b.filter(
                fin_period_end_date=finances_ar.fin_period_end_date
            ).first()
            if finances_ar
            else None
        )
        return {
            "ar": finances_ar,
            "parta": finances_parta,
            "partb": finances_partb,
        }

    def get_related_charities(self):
        """
        Yields tuple of (relationship, charity, note)
        """

        # subsidiaries
        subsids = Charity.objects.filter(
            registered_charity_number=self.registered_charity_number,
        ).exclude(
            organisation_number=self.organisation_number,
        )
        for s in subsids:
            yield (
                "Subsidiary" if s.linked_charity_number else "Parent",
                s,
                "",
            )

        # event history
        for s in self.event_history.filter(assoc_organisation_number__isnull=False):
            assoc_charity = Charity.objects.filter(
                organisation_number=s.assoc_organisation_number
            ).first()
            if not assoc_charity:
                continue
            yield (
                s.event_type,
                assoc_charity,
                " (on {}{})".format(
                    s.date_of_event,
                    " - {}".format(s.reason) if s.reason else "",
                ),
            )

        #
        for m in self.merged_into.all():
            if m.transferee:
                yield (
                    "Merged into",
                    m.transferee,
                    " (on {})".format(
                        m.date_property_transferred,
                    ),
                )
        #
        for m in self.merged_from.all():
            if m.transferor:
                yield (
                    "Merged from",
                    m.transferor,
                    " (on {})".format(
                        m.date_property_transferred,
                    ),
                )

    class Meta:
        verbose_name = "Charity in England and Wales"
        verbose_name_plural = "Charities in England and Wales"
