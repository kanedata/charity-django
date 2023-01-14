from django.contrib import admin
from django.urls import reverse
from django.utils.html import escape, format_html_join, mark_safe
from django.utils.translation import gettext_lazy as _

from charity_django.ccew.models import (
    Charity,
    CharityAnnualReturnHistory,
    CharityAreaOfOperation,
    CharityARPartA,
    CharityARPartB,
    CharityEventHistory,
    Merger,
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


class CharityAnnualReturnHistoryInline(CharityTabularInline):
    model = CharityAnnualReturnHistory


class CharityAreaOfOperationInline(CharityTabularInlineWithLinked):
    model = CharityAreaOfOperation


class CharityARPartAInline(admin.TabularInline):
    exclude = (
        "registered_charity_number",
        "date_of_extract",
        "latest_fin_period_submitted_ind",
        "fin_period_order_number",
        "ar_cycle_reference",
    )
    model = CharityARPartA


class CharityARPartBInline(admin.TabularInline):
    exclude = (
        "registered_charity_number",
        "date_of_extract",
        "latest_fin_period_submitted_ind",
        "fin_period_order_number",
        "ar_cycle_reference",
    )
    model = CharityARPartB


class CharityEventHistoryInline(admin.TabularInline):
    exclude = (
        "registered_charity_number",
        "linked_charity_number",
        "date_of_extract",
        "charity_name",
        "charity_event_order",
    )
    model = CharityEventHistory

    def get_queryset(self, request):
        return (
            super().get_queryset(request).filter(assoc_organisation_number__isnull=True)
        )


@admin.register(Charity)
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
        CharityAreaOfOperationInline,
        CharityAnnualReturnHistoryInline,
        CharityARPartAInline,
        CharityARPartBInline,
        CharityEventHistoryInline,
    ]
    readonly_fields = (
        "org_id",
        "chair",
        "trustees",
        "policies",
        "other_names",
        "related_charities",
        "how",
        "who",
        "what",
        "governing_document_description",
        "charitable_objects",
        "area_of_benefit",
        "regulators",
        "ccew_reports",
    )

    def trustees(self, obj):
        trustees = sorted(
            obj.trustees.all(),
            key=lambda s: (~s.trustee_is_chair, s.sort_name),
        )

        return format_html_join(
            "\n",
            "<li>{}{}{}</li>",
            (
                (
                    s.trustee_name,
                    " (Chair)" if s.trustee_is_chair else "",
                    " - appointed on {}".format(s.trustee_date_of_appointment)
                    if s.trustee_date_of_appointment
                    else "",
                )
                for s in trustees
            ),
        )

    def policies(self, obj):
        return format_html_join(
            "\n",
            "<li>{}</li>",
            [(o,) for o in obj.policies.values_list("policy_name", flat=True)],
        )

    def other_names(self, obj):
        return format_html_join(
            "\n",
            "<li>{} ({})</li>",
            [(n.charity_name, n.charity_name_type) for n in obj.other_names.all()],
        )

    def related_charities(self, obj):
        related_charities = [
            (
                s[0],
                reverse(
                    "admin:%s_%s_change"
                    % (s[1]._meta.app_label, s[1]._meta.model_name),
                    args=(s[1].pk,),
                ),
                str(s[1]),
                s[2],
            )
            for s in obj.get_related_charities()
        ]
        return format_html_join(
            "\n",
            '<li>{}: <a href="{}">{}</a>{}</li>',
            related_charities,
        )

    def what(self, obj):
        return format_html_join(
            "\n",
            "<li>{}</li>",
            [(o,) for o in obj.what],
        )

    def how(self, obj):
        return format_html_join(
            "\n",
            "<li>{}</li>",
            [(o,) for o in obj.how],
        )

    def who(self, obj):
        return format_html_join(
            "\n",
            "<li>{}</li>",
            [(o,) for o in obj.who],
        )

    def regulators(self, obj):
        return format_html_join(
            "\n",
            '<li><a href="{}" target="_blank">{}</a></li>',
            (
                (
                    s.regulator_web_url,
                    s.regulator_name,
                )
                for s in obj.other_regulators.all()
            ),
        )

    def ccew_reports(self, obj):
        return format_html_join(
            "\n",
            '<li><a href="{}" target="_blank">{}</a> ({})</li>',
            (
                (
                    s.report_location,
                    s.report_name,
                    s.date_published,
                )
                for s in obj.published_reports.all()
            ),
        )

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


@admin.register(Merger)
class MergerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "transferor_str",
        "transferee_str",
        "date_property_transferred",
    )

    def transferor_str(self, obj: Merger):
        assoc_charity = obj.transferor
        if not assoc_charity:
            return obj.transferor_name
        link = reverse(
            "admin:%s_%s_change"
            % (
                assoc_charity._meta.app_label,
                assoc_charity._meta.model_name,
            ),
            args=(assoc_charity.pk,),
        )
        return mark_safe(f'<a href="{link}">{escape(str(assoc_charity))}</a>')

    transferor_str.short_description = "Transferor"
    transferor_str.admin_order_field = "transferor_name"  # Make row sortable

    def transferee_str(self, obj: Merger):
        assoc_charity = obj.transferee
        if not assoc_charity:
            return obj.transferee_name
        link = reverse(
            "admin:%s_%s_change"
            % (
                assoc_charity._meta.app_label,
                assoc_charity._meta.model_name,
            ),
            args=(assoc_charity.pk,),
        )
        return mark_safe(f'<a href="{link}">{escape(str(assoc_charity))}</a>')

    transferee_str.short_description = "Transferee"
    transferee_str.admin_order_field = "transferee_name"  # Make row sortable

    def has_change_permission(self, request, obj=None):
        return False
