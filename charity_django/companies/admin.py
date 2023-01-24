from django.contrib import admin
from django.db.models import Count

from charity_django.companies.models import Company, SICCode
from charity_django.utils.admin import ReadOnlyMixin, UsedChoicesFieldListFilter


@admin.register(Company)
class CompanyAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = (
        "CompanyNumber",
        "CompanyName",
        "CompanyStatus",
        "CompanyCategory",
        "sic_codes_labels",
    )
    list_display_links = (
        "CompanyNumber",
        "CompanyName",
    )
    list_filter = (
        ("CompanyStatus", UsedChoicesFieldListFilter),
        ("CompanyCategory", UsedChoicesFieldListFilter),
        "sic_codes__sic_code",
    )
    search_fields = (
        "CompanyNumber",
        "CompanyName",
    )
    readonly_fields = ("sic_codes_labels",)

    @admin.display(description="SIC Codes")
    def sic_codes_labels(self, obj):
        return "; ".join(
            [
                f"{c.sic_code.title} [{c.sic_code.code}]"
                for c in obj.sic_codes.prefetch_related("sic_code").all()
            ]
        )


@admin.register(SICCode)
class SICCodeAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = (
        "code",
        "title",
        "companies_count",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(company_count=Count("companies", distinct=True))

    @admin.display(description="Companies", ordering="company_count")
    def companies_count(self, obj):
        return obj.companies.count()
