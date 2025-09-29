from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join, mark_safe

from charity_django.postcodes.models import GeoCode, GeoEntity, GeoEntityGroup, Postcode


class GeoEntityInlineAdmin(admin.TabularInline):
    model = GeoEntity
    fields = ("name", "code", "theme", "coverage", "status")
    extra = 0

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(GeoEntityGroup)
class GeoEntityGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    ordering = ("name",)
    inlines = (GeoEntityInlineAdmin,)

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(GeoEntity)
class GeoEntityAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "theme",
        "coverage",
        "status",
        "group",
    )
    ordering = ("code",)
    list_filter = (
        "theme",
        "status",
        "coverage",
    )
    search_fields = ("name", "code")

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Postcode)
class PostcodeAdmin(admin.ModelAdmin):
    list_display = ("PCDS", "local_authority", "region", "country", "DOINTR", "DOTERM")
    search_fields = ("PCDS",)
    list_filter = ("country", "region")
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "PCD",
                    "DOINTR",
                    "DOTERM",
                    "latlng",
                ],
            },
        ),
        (
            "Key areas",
            {
                "fields": [
                    "ward",
                    "local_authority",
                    "county",
                    "region",
                    "country",
                    "parlimentary_constitutency",
                ],
            },
        ),
        (
            "Census 2021",
            {
                "fields": [
                    "output_area_2021",
                    "lsoa2021",
                    "msoa2021",
                ],
            },
        ),
        (
            "Census 2011",
            {
                "fields": [
                    "output_area_2011",
                    "lsoa2011",
                    "msoa2011",
                    "travel_to_work_area",
                    "workplace_zone_2011",
                    "builtup_area_2011",
                    "builtup_area_subdivision_2011",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Statistics",
            {
                "fields": [
                    "rural_description",
                    "oac11_category",
                    "index_of_multiple_deprivation",
                ],
            },
        ),
        (
            "Health",
            {
                "fields": [
                    "health_authority",
                    "nhs_england_region",
                    "primary_care_trust",
                    "cancer_alliance",
                    "integrated_care_board",
                    "sub_icb_location",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Other",
            {
                "fields": [
                    "national_park",
                    "international_territorial_level",
                    "police_force_area",
                    "county_electoral_division",
                    "european_electoral_region",
                    "tec_lec",
                    "local_enterprise_partnership_1",
                    "local_enterprise_partnership_2",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Details",
            {
                "fields": [
                    "PCD2",
                    "PCDS",
                    "USERTYPE",
                    "OSGRDIND",
                    "OSEAST1M",
                    "OSNRTH1M",
                    "postcode_parts",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    @admin.display(description="Latitude/Longitude")
    def latlng(self, obj):
        if obj.LAT is None or obj.LONG is None:
            return None
        return format_html(
            '<a href="https://geohack.toolforge.org/geohack.php?params={}_N_{}_E" target="_blank">{}, {}</a>',
            f"{obj.LAT:.5f}",
            f"{obj.LONG:.5f}",
            f"{obj.LAT:.5f}",
            f"{obj.LONG:.5f}",
        )

    @admin.display(description="Output Area Classification")
    def oac11_category(self, obj):
        if obj.OAC11:
            return f"{obj.OAC11}: {obj.oac11_category()}"

    @admin.display(description="Rural-Urban Classification")
    def rural_description(self, obj):
        rural = obj.rural21_description()
        if rural and len(rural) == 3:
            return format_html(
                "{} ({})</div><div class='help'>{}",
                *rural,
            )
        else:
            return obj.RU21IND

    @admin.display(description="Index of Multiple Deprivation (IMD)")
    def index_of_multiple_deprivation(self, obj):
        if obj.IMD:
            imd_max = obj.imd_max()
            return format_html(
                """
                    <p>Most deprived <meter id="imd" min="1" max="{}" low="{}" high="{}" optimum="{}" value="{}" style="width: 600px;">{} out of {}</meter> Least deprived</p>
                    <p>{} out of {} areas in {} (where 1 is the most deprived).</p>
                    <p>{} of areas in {} are more deprived than this one.</p>
                """,
                imd_max,
                imd_max * 0.25,
                imd_max * 0.75,
                imd_max,
                obj.IMD,
                obj.IMD,
                imd_max,
                f"{obj.IMD:,.0f}",
                f"{imd_max:,.0f}",
                obj.country.GEOGNM,
                f"{obj.IMD / imd_max:.1%}",
                obj.country.GEOGNM,
            )

    @admin.display(description="Postcode parts")
    def postcode_parts(self, obj):
        parts = obj.parts
        return format_html(
            """
            <table>
                <thead>
                    <tr>
                        <th colspan="2">Outward code</th>
                        <th colspan="2">Inward code</th>
                    </tr>
                    <tr>
                        <th>Area</th>
                        <th>District</th>
                        <th>Sector</th>
                        <th>Unit</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                    </tr>
                </tbody>
            </table>
            """,
            parts["area"],
            parts["district"],
            parts["sector"],
            parts["unit"],
        )

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(GeoCode)
class GeoCodeAdmin(admin.ModelAdmin):
    list_display = (
        "GEOGCD",
        "GEOGNM",
        "OPER_DATE",
        "TERM_DATE",
        "PARENTCD",
        "ENTITYCD",
        "OWNER",
        "STATUS",
    )
    list_filter = (
        "OWNER",
        "STATUS",
        "ENTITYCD",
    )
    ordering = ("GEOGCD",)
    search_fields = ("GEOGNM",)
    readonly_fields = ("hierarchy", "children", "siblings")

    def has_change_permission(self, request, obj=None):
        return False

    def hierarchy(self, obj):
        return format_html_join(
            "\n",
            '<li style="list-style: none; margin-left: {}px;{}">&gt; {} - <a href="{}">{}</a></li>',
            (
                (
                    i * 18,
                    " font-weight: bold;" if i == 0 else "",
                    p.ENTITYCD.name,
                    reverse(
                        "admin:{}_{}_change".format(
                            p._meta.app_label, p._meta.model_name
                        ),
                        args=(p.pk,),
                    ),
                    f"{p.GEOGNM} [{p.GEOGCD}]" if p.GEOGNM else p.GEOGCD,
                )
                for i, p in enumerate([obj] + obj.get_parents())
            ),
        )

    def children(self, obj):
        children = obj.get_children()
        children_by_type = {}
        for c in children:
            children_by_type.setdefault(c.ENTITYCD, []).append(c)

        return_html = ""
        return_html += "<ul style='margin-left: 0px;'>"
        for entity, children in children_by_type.items():
            return_html += format_html(
                '<li style="list-style: none; margin-left: 10px; margin-bottom: 16px;"><strong>{}</strong><ul style="margin-left: 0px; padding-left: 0px; columns: 3;">',
                entity.name,
            )
            return_html += format_html_join(
                "\n",
                '<li style="list-style: none; margin-left: 0px;"><a href="{}">{}</a></li>',
                (
                    (
                        reverse(
                            "admin:{}_{}_change".format(
                                p._meta.app_label, p._meta.model_name
                            ),
                            args=(p.pk,),
                        ),
                        f"{p.GEOGNM} [{p.GEOGCD}]" if p.GEOGNM else p.GEOGCD,
                    )
                    for i, p in enumerate(children[:100])
                ),
            )
            return_html += format_html("</li></ul>")
        return_html += "</ul>"
        return mark_safe(return_html)

    def siblings(self, obj):
        children = obj.get_siblings()
        children_by_type = {}
        for c in children:
            children_by_type.setdefault(c.ENTITYCD, []).append(c)

        return_html = ""
        return_html += "<ul style='margin-left: 0px;'>"
        for entity, children in children_by_type.items():
            return_html += format_html(
                '<li style="list-style: none; margin-left: 10px; margin-bottom: 16px;"><strong>{} for {}</strong><ul style="margin-left: 0px; padding-left: 0px; columns: 3;">',
                entity.name,
                obj.parent.GEOGNM,
            )
            return_html += format_html_join(
                "\n",
                '<li style="list-style: none; margin-left: 0px;"><a href="{}">{}</a></li>',
                (
                    (
                        reverse(
                            "admin:{}_{}_change".format(
                                p._meta.app_label, p._meta.model_name
                            ),
                            args=(p.pk,),
                        ),
                        f"{p.GEOGNM} [{p.GEOGCD}]" if p.GEOGNM else p.GEOGCD,
                    )
                    for i, p in enumerate(children[:100])
                ),
            )
            return_html += format_html("</li></ul>")
        return_html += "</ul>"
        return mark_safe(return_html)
