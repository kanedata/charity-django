from django.contrib import admin

from charity_django.ccni.models import Charity
from charity_django.utils.admin import CharitySizeListFilter


class CCNICharitySizeListFilter(CharitySizeListFilter):
    recent_income_field = "total_income"


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
