from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from charity_django.ccew.models import (
    Charity,
    CharityAnnualReturnHistory,
    CharityAreaOfOperation,
    CharityARPartA,
    CharityARPartB,
    CharityClassification,
    CharityEventHistory,
    CharityGoverningDocument,
    CharityOtherNames,
    CharityOtherRegulators,
    CharityPolicy,
    CharityPublishedReport,
    CharityTrustee,
)
from charity_django.utils.admin import CharitySizeListFilter


class CCEWCharitySizeListFilter(CharitySizeListFilter):
    recent_income_field = "latest_income"


class MainCharityListFilter(admin.SimpleListFilter):
    title = _("main charity")
    parameter_name = "main"

    def lookups(self, request, model_admin):
        return (
            (1, _("Main charity")),
            (0, _("Subsidiary")),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        if int(self.value()) == 0:
            return queryset.filter(linked_charity_number__gt=0)
        if int(self.value()) == 1:
            return queryset.filter(linked_charity_number=0)


class CharityTabularInline(admin.TabularInline):
    exclude = ("registered_charity_number", "date_of_extract")


class CharityTabularInlineWithLinked(admin.TabularInline):
    exclude = ("registered_charity_number", "linked_charity_number", "date_of_extract")


class CharityOtherNamesInline(CharityTabularInlineWithLinked):
    model = CharityOtherNames


class CharityAnnualReturnHistoryInline(CharityTabularInline):
    model = CharityAnnualReturnHistory


class CharityAreaOfOperationInline(CharityTabularInlineWithLinked):
    model = CharityAreaOfOperation


class CharityARPartAInline(CharityTabularInline):
    model = CharityARPartA


class CharityARPartBInline(CharityTabularInline):
    model = CharityARPartB


class CharityClassificationInline(CharityTabularInlineWithLinked):
    model = CharityClassification


class CharityEventHistoryInline(CharityTabularInlineWithLinked):
    model = CharityEventHistory


class CharityGoverningDocumentInline(CharityTabularInlineWithLinked):
    model = CharityGoverningDocument


class CharityOtherNamesInline(CharityTabularInlineWithLinked):
    model = CharityOtherNames


class CharityOtherRegulatorsInline(CharityTabularInline):
    model = CharityOtherRegulators


class CharityPolicyInline(CharityTabularInlineWithLinked):
    model = CharityPolicy


class CharityPublishedReportInline(CharityTabularInlineWithLinked):
    model = CharityPublishedReport


class CharityTrusteeInline(CharityTabularInlineWithLinked):
    model = CharityTrustee


class CharityAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "registered_charity_number",
        "linked_charity_number",
        "charity_registration_status",
        "charity_type",
        "income",
    )
    list_display_links = ("name",)
    list_filter = (
        MainCharityListFilter,
        "charity_registration_status",
        CCEWCharitySizeListFilter,
        "charity_type",
    )
    ordering = (
        "registered_charity_number",
        "linked_charity_number",
    )
    search_fields = (
        "charity_name",
        "registered_charity_number",
    )
    inlines = [
        CharityAnnualReturnHistoryInline,
        CharityAreaOfOperationInline,
        CharityARPartAInline,
        CharityARPartBInline,
        CharityClassificationInline,
        CharityEventHistoryInline,
        CharityGoverningDocumentInline,
        CharityOtherNamesInline,
        CharityOtherRegulatorsInline,
        CharityPolicyInline,
        CharityPublishedReportInline,
        CharityTrusteeInline,
    ]

    def has_change_permission(self, request, obj=None):
        return False

    def income(self, obj):
        if obj.latest_income is None:
            return None
        return "£{:,.0f} (FYE {:%b %Y})".format(
            obj.latest_income,
            obj.latest_acc_fin_period_end_date,
        )

    income.admin_order_field = "latest_income"


admin.site.register(Charity, CharityAdmin)
