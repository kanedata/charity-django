from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from charity_django.utils.models import CommandLog


class ReadOnlyMixin:
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class CharitySizeListFilter(admin.SimpleListFilter):
    recent_income_field = "total_income"
    title = _("charity size")
    parameter_name = "size"

    size_bands = (
        (0, -1, 0, _("Zero income")),
        (1, 0, 10_000, _("Under £10,000")),
        (2, 10_000, 100_000, _("£10k - £100k")),
        (3, 100_000, 1_000_000, _("£100k - £1m")),
        (4, 1_000_000, 10_000_000, _("£1m - £10m")),
        (5, 10_000_000, 100_000_000, _("£10m - £100m")),
        (6, 100_000_000, None, _("Over £100m")),
    )

    def lookups(self, request, model_admin):
        return (("unknown", _("Unknown")),) + tuple(
            (str(band[0]), band[3]) for band in self.size_bands
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        if self.value() == "unknown":
            return queryset.filter(
                **{
                    f"{self.recent_income_field}__isnull": True,
                }
            )
        for band in self.size_bands:
            if self.value() == str(band[0]):
                if band[2] is None:
                    return queryset.filter(
                        **{
                            f"{self.recent_income_field}__gte": band[1],
                        }
                    )
                else:
                    return queryset.filter(
                        **{
                            f"{self.recent_income_field}__range": (
                                band[1] + 1,
                                band[2],
                            ),
                        }
                    )
        return queryset


class UsedChoicesFieldListFilter(admin.filters.ChoicesFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        self.lookup_choices = list(
            model_admin.get_queryset(request)
            .values_list(self.field_path, flat=True)
            .distinct()
        )

    def choices(self, changelist):
        yield {
            "selected": self.lookup_val is None,
            "query_string": changelist.get_query_string(
                remove=[self.lookup_kwarg, self.lookup_kwarg_isnull]
            ),
            "display": "All",
        }
        none_title = ""
        for lookup, title in self.field.flatchoices:
            if lookup is None:
                none_title = title
                continue
            if lookup not in self.lookup_choices:
                continue
            yield {
                "selected": str(lookup) == self.lookup_val,
                "query_string": changelist.get_query_string(
                    {self.lookup_kwarg: lookup}, [self.lookup_kwarg_isnull]
                ),
                "display": title,
            }
        if none_title:
            yield {
                "selected": bool(self.lookup_val_isnull),
                "query_string": changelist.get_query_string(
                    {self.lookup_kwarg_isnull: "True"}, [self.lookup_kwarg]
                ),
                "display": none_title,
            }


@admin.register(CommandLog)
class CommandLogAdmin(admin.ModelAdmin):
    list_display = (
        "command",
        "cmd_options",
        "started",
        "completed",
        "status",
        "has_log",
    )
    list_filter = ("status", "command", "started")
    search_fields = ("command", "cmd_options", "log")
    date_hierarchy = "started"

    readonly_fields = (
        "command",
        "cmd_options",
        "started",
        "completed",
        "status",
        "log",
    )

    @admin.display(description=_("Has log"), boolean=True)
    def has_log(self, obj):
        return bool(obj.log)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    class Media:
        css = {"all": ("admin/css/command_log.css",)}
