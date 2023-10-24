import re

from django.db import models

from charity_django.postcodes.codes import OAC11_SUBGROUPS, RURAL_URBAN_IND


class GeoEntityGroup(models.Model):
    code = models.CharField(
        max_length=32, verbose_name="Entity group code", primary_key=True
    )
    name = models.CharField(
        null=True, blank=True, verbose_name="Entity group name", max_length=255
    )

    def __str__(self):
        return f"{self.name} [{self.code}]"

    class Meta:
        verbose_name = "Area type group"
        verbose_name_plural = "Area type groups"


class GeoEntity(models.Model):
    class EntityStatus(models.TextChoices):
        CURRENT = "Current"
        ARCHIVED = "Archived"

    class EntityCoverage(models.TextChoices):
        ENGLAND = "England"
        ENGLAND_AND_WALES = "England and Wales"
        UNITED_KINGDOM = "United Kingdom"
        GREAT_BRITAIN = "Great Britain"
        CHANNEL_ISLANDS = "Channel Islands"
        ISLE_OF_MAN = "Isle of Man"
        NORTHERN_IRELAND = "Northern Ireland"
        SCOTLAND = "Scotland"
        WALES = "Wales"

    class EntityTheme(models.TextChoices):
        STATISTICAL_BUILDING_BLOCK = "Statistical Building Block"
        ADMINISTRATIVE = "Administrative"
        ADMINISTRATIVE_ELECTORAL = "Administrative/Electoral"
        ELECTORAL = "Electoral"
        HEALTH = "Health"
        OTHER = "Other"
        CENSUS = "Census"
        EXPERIMENTAL = "Experimental"
        HOUSING_AND_REGENERATION = "Housing and Regeneration"
        TRANSPORT = "Transport"
        ECONOMIC = "Economic"

    code = models.CharField(verbose_name="Entity code", max_length=3, primary_key=True)
    name = models.CharField(
        null=True, blank=True, verbose_name="Entity name", max_length=255, db_index=True
    )
    abbreviation = models.CharField(
        null=True, blank=True, verbose_name="Entity abbreviation", max_length=255
    )
    theme = models.CharField(
        null=True,
        blank=True,
        verbose_name="Entity theme",
        choices=EntityTheme.choices,
        max_length=32,
    )
    coverage = models.CharField(
        null=True,
        blank=True,
        verbose_name="Entity coverage",
        choices=EntityCoverage.choices,
        max_length=32,
    )
    related_entities = models.ManyToManyField(
        "self", blank=True, verbose_name="Related entity codes", symmetrical=False
    )
    status = models.CharField(
        null=True,
        blank=True,
        verbose_name="Status",
        choices=EntityStatus.choices,
        max_length=8,
    )
    n_live = models.IntegerField(
        null=True, blank=True, verbose_name="Number of live instances"
    )
    n_archived = models.IntegerField(
        null=True, blank=True, verbose_name="Number of archived instances"
    )
    n_crossborder = models.IntegerField(
        null=True, blank=True, verbose_name="Number of cross-border instances"
    )
    last_changed = models.DateField(
        null=True, blank=True, verbose_name="Date of last instance change"
    )
    first_code = models.CharField(
        max_length=9,
        null=True,
        blank=True,
        verbose_name="Current code (first in range)",
    )
    last_code = models.CharField(
        max_length=9, null=True, blank=True, verbose_name="Current code (last in range)"
    )
    reserved_code = models.CharField(
        max_length=9, null=True, blank=True, verbose_name="Reserved code (for CHD use)"
    )
    owner = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Entity owner abbreviation"
    )
    date_introduced = models.DateField(
        null=True, blank=True, verbose_name="Date entity introduced on RGC"
    )
    start_date = models.DateField(
        null=True, blank=True, verbose_name="Entity start date"
    )
    group = models.ForeignKey(
        GeoEntityGroup,
        null=True,
        blank=True,
        verbose_name="Entity group",
        on_delete=models.SET_NULL,
        related_name="entities",
    )

    def __str__(self):
        return f"{self.name} [{self.code}]"

    class Meta:
        verbose_name = "Area type"
        verbose_name_plural = "Area types"


class GeoCode(models.Model):
    class Status(models.TextChoices):
        LIVE = "live"
        TERMINATED = "terminated"

    GEOGCD = models.CharField(max_length=9, verbose_name="Area code", primary_key=True)
    GEOGNM = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Area name",
        db_index=True,
    )
    GEOGNMW = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Area name (Welsh)"
    )
    SI_ID = models.CharField(
        max_length=9, null=True, blank=True, verbose_name="Statutory Instrument ID"
    )
    SI_TITLE = models.TextField(
        null=True, blank=True, verbose_name="Statutory Instrument title"
    )
    OPER_DATE = models.DateField(null=True, blank=True, verbose_name="Operational date")
    TERM_DATE = models.DateField(null=True, blank=True, verbose_name="Termination date")
    PARENTCD = models.CharField(
        max_length=9, null=True, blank=True, verbose_name="Parent code"
    )
    ENTITYCD = models.ForeignKey(
        GeoEntity,
        related_name="geo_codes",
        max_length=3,
        null=True,
        blank=True,
        verbose_name="Entity code",
        on_delete=models.SET_NULL,
    )
    OWNER = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Owner"
    )
    STATUS = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Status",
        choices=Status.choices,
    )
    AREAEHECT = models.FloatField(
        null=True,
        blank=True,
        verbose_name="'Extent of the Realm' measurement, in hectares",
    )
    AREACHECT = models.FloatField(
        null=True, blank=True, verbose_name="Area to Mean High Water, in hectares"
    )
    AREAIHECT = models.FloatField(
        null=True, blank=True, verbose_name="Area of inland water, in hectares"
    )
    AREALHECT = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Area to Mean High Water excluding area of inland water (land area), in hectares",
    )

    @property
    def code(self):
        return self.GEOGCD

    @property
    def name(self):
        return self.GEOGNM

    @property
    def parent(self):
        if self.PARENTCD:
            return GeoCode.objects.get(GEOGCD=self.PARENTCD)

    def get_parents(self):
        parents = []
        parent = self
        while parent.PARENTCD:
            parent = GeoCode.objects.get(GEOGCD=parent.PARENTCD)
            parents.append(parent)
        return parents

    def get_children(self):
        return GeoCode.objects.filter(PARENTCD=self.GEOGCD)

    def get_siblings(self):
        return GeoCode.objects.filter(
            PARENTCD=self.PARENTCD, ENTITYCD=self.ENTITYCD
        ).exclude(GEOGCD=self.GEOGCD)

    def __str__(self):
        if self.GEOGNM:
            return "{}: {}".format(self.GEOGCD, self.GEOGNM)
        return "{}".format(self.GEOGCD)

    class Meta:
        verbose_name = "Area"
        verbose_name_plural = "Areas"


class Postcode(models.Model):
    class UserTypes(models.IntegerChoices):
        SMALL_USER = 0
        LARGE_USER = 1

    class PositionalQualityIndicators(models.IntegerChoices):
        WITHIN_BUILDING = 1  # = within the building of the matched address closest to the postcode mean;
        WITHIN_BUILDING_VISUAL = 2  # = as for status value 1, except by visual inspection of Landline maps (Scotland only);
        APPROXIMATE = 3  # = approximate to within 50 metres;
        POSTCODE_UNIT_MEAN = 4  # = postcode unit mean (mean of matched addresses with the same postcode, but not snapped to a building);
        IMPUTED = (
            5  # = imputed by ONS, by reference to surrounding postcode grid references;
        )
        POSTCODE_SECTOR_MEAN = 6  # = postcode sector mean, (mainly PO Boxes);
        TERMINATED = 8  # = postcode terminated prior to Gridlink® initiative, last known ONS postcode grid reference2;
        NONE_AVAILABLE = 9  # = no grid reference available

    postcode_regex = re.compile(
        r"^(?P<area>[A-Z]{1,2})(?P<district>[0-9][A-Z0-9]?) ?(?P<sector>[0-9])(?P<unit>[A-Z]{2})$"
    )

    PCD = models.CharField(
        max_length=7,
        help_text="Unit postcode – 7 character version",
        verbose_name="Postcode",
        primary_key=True,
    )
    PCD2 = models.CharField(
        max_length=8,
        null=True,
        blank=True,
        help_text="Unit postcode – 8 character version",
    )
    PCDS = models.CharField(
        max_length=8,
        null=True,
        blank=True,
        help_text="8 Unit postcode - variable length (e-Gif) version",
        db_index=True,
    )
    DOINTR = models.CharField(
        max_length=6, null=True, blank=True, verbose_name="Date of introduction"
    )
    DOTERM = models.CharField(
        max_length=6, null=True, blank=True, verbose_name="Date of termination"
    )
    USERTYPE = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="User type",
        choices=UserTypes.choices,
    )
    OSEAST1M = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Easting",
        help_text="National grid reference - Easting",
    )
    OSNRTH1M = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Northing",
        help_text="National grid reference - Northing",
    )
    OSGRDIND = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Positional quality",
        help_text="Grid reference positional quality indicator",
        choices=PositionalQualityIndicators.choices,
    )
    output_area_2011 = models.ForeignKey(
        GeoCode,
        db_column="OA11",
        related_name="oa11_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="Output Area 2011",
    )
    county = models.ForeignKey(
        GeoCode,
        db_column="CTY",
        related_name="cty_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="County",
    )
    county_electoral_division = models.ForeignKey(
        GeoCode,
        db_column="CED",
        related_name="ced_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="County Electoral Division",
    )
    local_authority = models.ForeignKey(
        GeoCode,
        db_column="LAUA",
        related_name="laua_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Local Authority",
        limit_choices_to={
            "ENTITYCD__code__in": ["E06", "E07", "E08", "E09", "N09", "S12", "W06"]
        },
        help_text="Local Authority District (LAD) - unitary authority (UA)/non-metropolitan district (NMD)/ metropolitan district (MD)/ London borough (LB)/ council area (CA)/district council area (DCA)",
    )
    ward = models.ForeignKey(
        GeoCode,
        db_column="WARD",
        related_name="ward_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="(Electoral) ward/division",
        limit_choices_to={"ENTITYCD__code__in": ["E05", "N08", "S13", "W05"]},
    )
    health_authority = models.ForeignKey(
        GeoCode,
        db_column="HLTHAU",
        related_name="hlthau_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        limit_choices_to={"ENTITYCD__code__in": ["E18"]},
        help_text="Former Strategic Health Authority (SHA)/ Local Health Board (LHB)/ Health Board (HB)/ Health Authority (HA)/ Health & Social Care Board (HSCB)",
    )
    nhs_england_region = models.ForeignKey(
        GeoCode,
        db_column="NHSER",
        related_name="nhser_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        help_text="NHS England (Region) (NHS ER)",
        limit_choices_to={"ENTITYCD__code__in": ["E40"]},
        verbose_name="NHS England Region",
    )
    country = models.ForeignKey(
        GeoCode,
        db_column="CTRY",
        related_name="ctry_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        db_index=True,
        null=True,
        blank=True,
        limit_choices_to={"ENTITYCD__code__in": ["E92", "N92", "S92", "W92"]},
    )
    region = models.ForeignKey(
        GeoCode,
        db_column="RGN",
        related_name="rgn_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        help_text="Region (former GOR)",
        limit_choices_to={"ENTITYCD__code__in": ["E12"]},
    )
    parlimentary_constitutency = models.ForeignKey(
        GeoCode,
        db_column="PCON",
        related_name="pcon_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        help_text="Westminster parliamentary constituency",
    )
    european_electoral_region = models.ForeignKey(
        GeoCode,
        db_column="EER",
        related_name="eer_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        help_text="European Electoral Region (EER)",
    )
    tec_lec = models.ForeignKey(
        GeoCode,
        db_column="TECLEC",
        related_name="teclec_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="Learning and Skills Council",
        help_text="Local Learning and Skills Council (LLSC)/ Dept. of Children, Education, Lifelong Learning and Skills (DCELLS)/ Enterprise Region (ER)",
    )
    travel_to_work_area = models.ForeignKey(
        GeoCode,
        db_column="TTWA",
        related_name="ttwa_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="Travel to Work Area (TTWA)",
    )
    primary_care_trust = models.ForeignKey(
        GeoCode,
        db_column="PCT",
        related_name="pct_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        help_text="Primary Care Trust (PCT)/ Care Trust/ Care Trust Plus (CT)/ Local Health Board (LHB)/ Community Health Partnership (CHP)/ Local Commissioning Group (LCG)/ Primary Healthcare Directorate (PHD)",
    )
    international_territorial_level = models.ForeignKey(
        GeoCode,
        db_column="ITL",
        related_name="itl_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        help_text="International Territorial Level (former NUTS)",
    )
    national_park = models.ForeignKey(
        GeoCode,
        db_column="PARK",
        related_name="park_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
    )
    lsoa2011 = models.ForeignKey(
        GeoCode,
        db_column="LSOA11",
        related_name="lsoa11_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="LSOA 2011",
        help_text="2011 Census Lower Layer Super Output Area (LSOA)/ Data Zone (DZ)/ SOA",
    )
    msoa2011 = models.ForeignKey(
        GeoCode,
        db_column="MSOA11",
        related_name="msoa11_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="MSOA 2011",
        help_text="2011 Census Middle Layer Super Output Area (MSOA)/ Intermediate Zone (IZ)",
    )
    workplace_zone_2011 = models.ForeignKey(
        GeoCode,
        db_column="WZ11",
        related_name="wz11_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="2011 Census Workplace Zone",
    )
    sub_icb_location = models.ForeignKey(
        GeoCode,
        db_column="SICBL",
        related_name="sicbl_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="Sub ICB Location",
        help_text="Sub ICB Location (SICBL)/ Local Health Board (LHB)/ Community Health Partnership (CHP)/ Local Commissioning Group (LCG)/ Primary Healthcare Directorate (PHD)",
    )
    builtup_area_2011 = models.ForeignKey(
        GeoCode,
        db_column="BUA11",
        related_name="bua11_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="Built-up Area (BUA)",
    )
    builtup_area_subdivision_2011 = models.ForeignKey(
        GeoCode,
        db_column="BUASD11",
        related_name="buasd11_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="Built-up Area Sub-division (BUASD)",
    )
    RU11IND = models.CharField(
        max_length=2,
        null=True,
        blank=True,
        verbose_name="2011 Census rural-urban classification",
    )
    OAC11 = models.CharField(
        max_length=9,
        null=True,
        blank=True,
        verbose_name="2011 Census Output Area classification (OAC)",
    )
    LAT = models.FloatField(null=True, blank=True, verbose_name="Latitude")
    LONG = models.FloatField(null=True, blank=True, verbose_name="Longitude")
    local_enterprise_partnership_1 = models.ForeignKey(
        GeoCode,
        db_column="LEP1",
        related_name="lep1_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        help_text="Local Enterprise Partnership (LEP) - first instance",
    )
    local_enterprise_partnership_2 = models.ForeignKey(
        GeoCode,
        db_column="LEP2",
        related_name="lep2_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        help_text="Local Enterprise Partnership (LEP) - second instance",
    )
    police_force_area = models.ForeignKey(
        GeoCode,
        db_column="PFA",
        related_name="pfa_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="Police Force Area (PFA)",
    )
    IMD = models.IntegerField(
        null=True, blank=True, verbose_name="Index of Multiple Deprivation (IMD)"
    )
    cancer_alliance = models.ForeignKey(
        GeoCode,
        db_column="CALNCV",
        related_name="calncv_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="Cancer Alliance (CAL)",
    )
    integrated_care_board = models.ForeignKey(
        GeoCode,
        db_column="ICB",
        related_name="icb_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="Integrated Care Board (ICB)",
    )
    output_area_2021 = models.ForeignKey(
        GeoCode,
        db_column="OA21",
        related_name="oa21_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="Output Area 2021",
        help_text="2021 Census Output Area (OA)/ Small Area (SA)",
    )
    lsoa2021 = models.ForeignKey(
        GeoCode,
        db_column="LSOA21",
        related_name="lsoa21_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="LSOA 2021",
        help_text="2021 Census Lower Layer Super Output Area (LSOA)/ Data Zone (DZ)/ SOA",
    )
    msoa2021 = models.ForeignKey(
        GeoCode,
        db_column="MSOA21",
        related_name="msoa21_postcodes",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        max_length=9,
        null=True,
        blank=True,
        verbose_name="LSOA 2021",
        help_text="2021 Census Middle Layer Super Output Area (MSOA)/ Intermediate Zone (IZ)",
    )

    def __str__(self):
        return self.PCDS

    @property
    def outward_code(self):
        parts = self.postcode_regex.match(self.PCD)
        return parts.group("area") + parts.group("district")

    @property
    def inward_code(self):
        parts = self.postcode_regex.match(self.PCD)
        return parts.group("sector") + parts.group("unit")

    @property
    def postcode_area(self):
        parts = self.postcode_regex.match(self.PCD)
        return parts.group("area")

    @property
    def postcode_district(self):
        parts = self.postcode_regex.match(self.PCD)
        return parts.group("area") + parts.group("district")

    @property
    def postcode_sector(self):
        parts = self.postcode_regex.match(self.PCD)
        return (
            parts.group("area") + parts.group("district") + " " + parts.group("sector")
        )

    @property
    def parts(self):
        return self.postcode_regex.match(self.PCD).groupdict()

    def oac11_subgroup(self):
        if self.OAC11:
            return OAC11_SUBGROUPS.get(self.OAC11)[0]

    def oac11_group(self):
        if self.OAC11:
            return OAC11_SUBGROUPS.get(self.OAC11)[1]

    def oac11_supergroup(self):
        if self.OAC11:
            return OAC11_SUBGROUPS.get(self.OAC11)[2]

    def oac11_category(self):
        if self.OAC11:
            return " > ".join(OAC11_SUBGROUPS.get(self.OAC11)[::-1])

    def rural_description(self):
        if self.RU11IND:
            return RURAL_URBAN_IND.get(self.RU11IND)

    def imd_max(self):
        """
        England
        The 2019 IMD ranks each English LSOA from 1 (most deprived) to
        32,844 (least deprived).

        Wales
        The 2019 Welsh equivalent (WIMD) ranks each Welsh LSOA from 1
        (most deprived) to 1,909 (least deprived).

        Scotland
        The 2020 Scottish equivalent (SIMD), based on 2011 Census DZs,
        ranks each DZ from 1 (most deprived) to 6,976 (least deprived).

        Northern Ireland
        The 2017 NI equivalent based on 2001 SAs (unchanged for 2011)
        ranks each SA from 1 (most deprived) to 890 (least deprived).

        """
        if self.IMD:
            if self.country_id == "E92000001":
                return 32844
            elif self.country_id == "N92000002":
                return 1909
            elif self.country_id == "S92000003":
                return 6976
            elif self.country_id == "N92000001":
                return 890
