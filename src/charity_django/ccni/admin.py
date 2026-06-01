from django.contrib import admin
from django.utils.html import format_html_join

from charity_django.ccni.models import Charity, CharityFinancialYear
from charity_django.utils.admin import CharitySizeListFilter


class CCNICharitySizeListFilter(CharitySizeListFilter):
    recent_income_field = "total_income"


class CharityFinancialYearInline(admin.TabularInline):
    exclude = []
    model = CharityFinancialYear


class CharityAdmin(admin.ModelAdmin):
    list_display = (
        "charity_name",
        "reg_charity_number",
        "status",
    )
    list_display_links = ("charity_name",)
    list_filter = (
        "status",
        CCNICharitySizeListFilter,
    )
    ordering = ("reg_charity_number",)
    search_fields = (
        "charity_name",
        "reg_charity_number",
    )
    inlines = [
        CharityFinancialYearInline,
    ]
    exclude = [
        "charitable_spending",
        "income_generation_and_governance",
        "financial_period_start",
        "financial_period_end",
        "total_income_previous_financial_period",
        "employed_staff",
        "uk_and_ireland_volunteers",
        "income_from_donations_and_legacies",
        "income_from_charitable_activities",
        "income_from_other_trading_activities",
        "income_from_investments",
        "income_from_other",
        "total_income_and_endowments",
        "expenditure_on_raising_funds",
        "expenditure_on_charitable_activities",
        "expenditure_on_governance",
        "expenditure_on_other",
        "total_expenditure",
        "assets_and_liabilities_total_fixed_assets",
        "total_net_assets_and_liabilities",
    ]
    readonly_fields = (
        "org_id",
        "what_the_charity_does",
        "how_the_charity_works",
        "who_the_charity_helps",
    )

    def what_the_charity_does(self, obj):
        return format_html_join(
            "\n",
            "<li>{}</li>",
            [(o,) for o in obj.what_the_charity_does],
        )

    def how_the_charity_works(self, obj):
        return format_html_join(
            "\n",
            "<li>{}</li>",
            [(o,) for o in obj.how_the_charity_works],
        )

    def who_the_charity_helps(self, obj):
        return format_html_join(
            "\n",
            "<li>{}</li>",
            [(o,) for o in obj.who_the_charity_helps],
        )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def income(self, obj):
        if obj.total_income is None:
            return None
        return "£{:,.0f} (FYE {:%b %Y})".format(
            obj.total_income,
            obj.date_for_financial_year_ending,
        )

    income.admin_order_field = "total_income"


admin.site.register(Charity, CharityAdmin)
