from django.db import models


class Merger(models.Model):
    transferor_name = models.CharField(max_length=255, null=True, blank=True)
    transferor_regno = models.IntegerField(null=True, blank=True, db_index=True)
    transferor_subno = models.IntegerField(null=True, blank=True, db_index=True)
    transferor = models.ForeignKey(
        "ccew.Charity",
        on_delete=models.CASCADE,
        verbose_name="Transferor",
        related_name="merged_into",
        null=True,
        blank=True,
    )
    transferee_name = models.CharField(max_length=255, null=True, blank=True)
    transferee_regno = models.IntegerField(null=True, blank=True, db_index=True)
    transferee_subno = models.IntegerField(null=True, blank=True, db_index=True)
    transferee = models.ForeignKey(
        "ccew.Charity",
        on_delete=models.CASCADE,
        verbose_name="Transferee",
        related_name="merged_from",
        null=True,
        blank=True,
    )
    date_vesting_declaration = models.DateField(max_length=255, null=True, blank=True)
    date_property_transferred = models.DateField(max_length=255, null=True, blank=True)
    date_merger_registered = models.DateField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Charity Merger"
        verbose_name_plural = "Register of Mergers"
