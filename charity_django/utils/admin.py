from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _


class CharitySizeListFilter(SimpleListFilter):
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
