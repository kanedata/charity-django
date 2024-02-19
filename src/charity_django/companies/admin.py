from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html_join

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
    )
    search_fields = (
        "CompanyNumber",
        "CompanyName",
    )
    readonly_fields = ("sic_codes_labels", "previous_name_labels", "accounts_labels")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "CompanyName",
                    "CompanyNumber",
                    "CompanyCategory",
                    "is_nonprofit",
                    "CompanyStatus",
                    "DissolutionDate",
                    "IncorporationDate",
                    "CountryOfOrigin",
                    "sic_codes_labels",
                    "previous_name_labels",
                    "last_updated",
                    "in_latest_update",
                )
            },
        ),
        (
            "Address",
            {
                "fields": (
                    "RegAddress_CareOf",
                    "RegAddress_POBox",
                    "RegAddress_AddressLine1",
                    "RegAddress_AddressLine2",
                    "RegAddress_PostTown",
                    "RegAddress_County",
                    "RegAddress_Country",
                    "RegAddress_PostCode",
                ),
            },
        ),
        (
            "Accounts",
            {
                "fields": (
                    "Accounts_AccountRefDay",
                    "Accounts_AccountRefMonth",
                    "Accounts_NextDueDate",
                    "Accounts_LastMadeUpDate",
                    "Accounts_AccountCategory",
                    "Returns_NextDueDate",
                    "Returns_LastMadeUpDate",
                    "accounts_labels",
                ),
            },
        ),
        (
            "Mortgages",
            {
                "fields": (
                    "Mortgages_NumMortCharges",
                    "Mortgages_NumMortOutstanding",
                    "Mortgages_NumMortPartSatisfied",
                    "Mortgages_NumMortSatisfied",
                ),
            },
        ),
        (
            "Other",
            {
                "fields": (
                    "LimitedPartnerships_NumGenPartners",
                    "LimitedPartnerships_NumLimPartners",
                    "ConfStmtNextDueDate",
                    "ConfStmtLastMadeUpDate",
                )
            },
        ),
    )

    @admin.display(description="SIC Codes")
    def sic_codes_labels(self, obj):
        return format_html_join(
            "\n",
            "<li>{} [{}]</li>",
            [
                (c.sic_code.title, c.sic_code.code)
                for c in obj.sic_codes.prefetch_related("sic_code").all()
            ],
        )

    @admin.display(description="Previous names")
    def previous_name_labels(self, obj):
        return format_html_join(
            "\n",
            "<li>{} [{}]</li>",
            [(c.CompanyName, c.ConDate) for c in obj.previous_names.all()],
        )

    @admin.display(description="Accounts")
    def accounts_labels(self, obj):
        return format_html_join(
            "\n",
            "<li>{} - {}</li>",
            [
                (c.financial_year_end, c.get_category_display())
                for c in obj.accounts.all()
            ],
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
