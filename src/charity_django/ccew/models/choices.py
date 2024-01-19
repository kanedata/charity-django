from django.db import models
from django.utils.translation import gettext_lazy as _


class CharityRegistrationStatus(models.TextChoices):
    REGISTERED = "Registered", _("Registered")
    REMOVED = "Removed", _("Removed")


class CharityType(models.TextChoices):
    CIO = "CIO", _("CIO")
    CHARITABLE_COMPANY = "Charitable company", _("Charitable company")
    OTHER = "Other", _("Other")
    PREVIOUSLY_EXCEPTED = "Previously excepted", _("Previously excepted")
    TRUST = "Trust", _("Trust")
    DEMONSTRATION_CHARITY = "Demonstration charity", _("Demonstration charity")


class CharityReportingStatus(models.TextChoices):
    NEW = "New", _("New")
    REMOVED = "Removed", _("Removed")
    SUBMISSION_DOUBLE_DEFAULT = (
        "Submission Double Default",
        _("Submission Double Default"),
    )
    SUBMISSION_OVERDUE = "Submission Overdue", _("Submission Overdue")
    SUBMISSION_RECEIVED = "Submission Received", _("Submission Received")
    SUBMISSION_RECEIVED_LATE = "Submission Received Late", _("Submission Received Late")
    SUPPRESSED = "Suppressed", _("Suppressed")


class CharityIsCDFOrCIF(models.TextChoices):
    CDF = "CDF", _("Common Deposit Fund")
    CIF = "CIF", _("Common Investment Fund")


class ClassificationType(models.TextChoices):
    WHAT = "What"
    HOW = "How"
    WHO = "Who"


class EventType(models.TextChoices):
    ASSET_TRANSFER_IN = "Asset transfer in", _("Asset transfer in")
    ASSET_TRANSFER_OUT = "Asset transfer out", _("Asset transfer out")
    CIO_REGISTRATION = "CIO registration", _("CIO registration")
    PREVIOUSLY_EXCEPTED_REGISTRATION = (
        "Previously excepted registration",
        _("Previously excepted registration"),
    )
    RE_REGISTERED = "Re-registered", _("Re-registered")
    REMOVED = "Removed", _("Removed")
    STANDARD_REGISTRATION = "Standard registration", _("Standard registration")


class CharityNameType(models.TextChoices):
    PREVIOUS_NAME = "Previous name", _("Previous name")
    WORKING_NAME = "Working name", _("Working name")


class IndividualOrOrganisation(models.TextChoices):
    INDIVIDUAL = "P"
    ORGANISATION = "O"
