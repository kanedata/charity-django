from django.contrib import admin
from django.utils.html import format_html_join
from django.utils.translation import gettext_lazy as _

from charity_django.oscr.models import (
    Charity,
    CharityClassification,
    CharityFinancialYear,
)
from charity_django.utils.admin import CharitySizeListFilter


class OSCRCharitySizeListFilter(CharitySizeListFilter):
    recent_income_field = "most_recent_year_income"


class CharityFinancialYearInline(admin.TabularInline):
    exclude = ("charity_number", "mailing_cycle")
    model = CharityFinancialYear


class CharityAdmin(admin.ModelAdmin):
    list_display = (
        "charity_name",
        "charity_number",
        "charity_status",
    )
    list_display_links = ("charity_name",)
    list_filter = (
        "charity_status",
        OSCRCharitySizeListFilter,
    )
    ordering = ("charity_number",)
    search_fields = (
        "charity_name",
        "charity_number",
    )
    inlines = [
        CharityFinancialYearInline,
    ]
    exclude = (
        "date_annual_return_received",
        "next_year_end_date",
        "donations_and_legacies_income",
        "charitable_activities_income",
        "other_trading_activities_income",
        "investments_income",
        "other_income",
        "raising_funds_spending",
        "charitable_activities_spending",
        "other_spending",
    )
    readonly_fields = (
        "org_id",
        "purposes",
        "activities",
        "beneficiaries",
    )

    def purposes(self, obj):
        return format_html_join(
            "\n",
            "<li>{}</li>",
            [(o,) for o in obj.purposes],
        )

    def activities(self, obj):
        return format_html_join(
            "\n",
            "<li>{}</li>",
            [(o,) for o in obj.activities],
        )

    def beneficiaries(self, obj):
        return format_html_join(
            "\n",
            "<li>{}</li>",
            [(o,) for o in obj.beneficiaries],
        )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def income(self, obj):
        if obj.most_recent_year_income is None:
            return None
        return "£{:,.0f} (FYE {:%b %Y})".format(
            obj.most_recent_year_income,
            obj.year_end,
        )

    income.admin_order_field = "most_recent_year_income"


admin.site.register(Charity, CharityAdmin)
