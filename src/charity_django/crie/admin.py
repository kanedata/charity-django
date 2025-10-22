from django.contrib import admin
from django.utils.html import format_html_join

from charity_django.crie.models import (
    Charity,
    CharityFinancialYear,
    ClassificationTypes,
)
from charity_django.utils.admin import CharitySizeListFilter


class CRIECharitySizeListFilter(CharitySizeListFilter):
    recent_income_field = "latest_income"


class CharityFinancialYearInline(admin.TabularInline):
    model = CharityFinancialYear
    extra = 0
    readonly_fields = (
        "period_start_date",
        "period_end_date",
        "income",
        "expenditure",
        "employees",
    )
    fields = readonly_fields
    ordering = ("-period_end_date",)

    def income(self, obj):
        if obj.gross_income is not None:
            return "€{:,.0f}".format(obj.gross_income)
        if obj.gross_income_schools is not None:
            return obj.gross_income_schools
        return None

    def expenditure(self, obj):
        if obj.gross_expenditure is not None:
            return "€{:,.0f}".format(obj.gross_expenditure)
        if obj.gross_expenditure_schools is not None:
            return obj.gross_expenditure_schools
        return None
        return None

    def employees(self, obj):
        if (
            obj.number_of_full_time_employees is not None
            or obj.number_of_part_time_employees is not None
        ):
            return "{:,.0f}".format(
                (obj.number_of_full_time_employees or 0)
                + (obj.number_of_part_time_employees or 0)
            )
        if obj.number_of_employees is not None:
            return obj.number_of_employees
        return None

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class CharityAdmin(admin.ModelAdmin):
    list_display = (
        "registered_charity_name",
        "registered_charity_number",
        "status",
        "income",
    )
    list_display_links = ("registered_charity_name",)
    list_filter = (
        "status",
        CRIECharitySizeListFilter,
    )
    ordering = ("registered_charity_number",)
    search_fields = (
        "registered_charity_name",
        "registered_charity_number",
    )
    readonly_fields = (
        "org_id",
        "also_known_as",
        "charitable_purposes",
        "charity_classifications",
        "operates_in",
        "beneficiaries",
        "report_activities",
    )
    exclude = (
        "classifications",
        "latest_activity_description_ga",
        "charitable_objects_ga",
    )
    inlines = (CharityFinancialYearInline,)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "registered_charity_number",
                    "org_ids",
                    ("registered_charity_name", "also_known_as"),
                    "status",
                    "latest_activity_description",
                )
            },
        ),
        (
            "Classifications",
            {
                "fields": (
                    "charity_classifications",
                    "beneficiaries",
                    "report_activities",
                )
            },
        ),
        (
            "Governance",
            {
                "fields": (
                    ("governing_form", "cro_number"),
                    "charitable_objects",
                    "charitable_purposes",
                )
            },
        ),
        (
            "Latest data",
            {
                "fields": (
                    "latest_financial_year_end",
                    "income",
                    "expenditure",
                )
            },
        ),
        (
            "Geography",
            {
                "fields": (
                    "primary_address",
                    "country_established",
                    "operates_in",
                )
            },
        ),
    )

    def _output_list(self, items):
        if not items:
            return "-"
        return format_html_join(
            "\n",
            "<li>{}</li>",
            ((item,) for item in items),
        )

    def org_ids(self, obj):
        return self._output_list(obj.org_ids)

    def also_known_as(self, obj):
        names = [(c.name,) for c in obj.names.exclude(name=obj.registered_charity_name)]
        return self._output_list(names)

    def _classification_list(self, obj, classification_field: ClassificationTypes):
        classifications = [
            (c.classification_en,)
            for c in obj.classifications.filter(
                classification_type=classification_field
            ).order_by("classification_en")
        ]
        return self._output_list(classifications)

    def charitable_purposes(self, obj):
        return self._classification_list(obj, ClassificationTypes.CHARITABLE_PURPOSE)

    def charity_classifications(self, obj):
        return self._classification_list(
            obj, ClassificationTypes.CHARITY_CLASSIFICATION
        )

    def operates_in(self, obj):
        return self._classification_list(obj, ClassificationTypes.OPERATES_IN)

    def beneficiaries(self, obj):
        return self._classification_list(obj, ClassificationTypes.BENEFICIARIES)

    def report_activities(self, obj):
        return self._classification_list(obj, ClassificationTypes.REPORT_ACTIVITY)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def income(self, obj):
        if obj.latest_income is None:
            return None
        return "€{:,.0f} (FYE {:%b %Y})".format(
            obj.latest_income,
            obj.latest_financial_year_end,
        )

    def expenditure(self, obj):
        if obj.latest_expenditure is None:
            return None
        return "€{:,.0f} (FYE {:%b %Y})".format(
            obj.latest_expenditure,
            obj.latest_financial_year_end,
        )

    income.admin_order_field = "latest_income"
    expenditure.admin_order_field = "latest_expenditure"


admin.site.register(Charity, CharityAdmin)
