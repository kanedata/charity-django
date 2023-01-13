from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from charity_django.oscr.models import Charity
from charity_django.utils.admin import CharitySizeListFilter


class OSCRCharitySizeListFilter(CharitySizeListFilter):
    recent_income_field = "most_recent_year_income"


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
