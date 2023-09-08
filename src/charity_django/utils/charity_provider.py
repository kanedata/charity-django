from faker.generator import Generator
from faker.providers import BaseProvider
from faker.providers.address import Provider as AddressProvider


class CharityProvider(BaseProvider):
    def __init__(self, generator: Generator) -> None:
        """Declare the other faker providers."""
        super().__init__(generator)
        self.address = AddressProvider(generator)

    charity_suffixes = (
        "Trust",
        "Society",
        "Foundation",
        "Trustees",
        "Cares",
        "Institute",
        "Association",
        "Charity",
        "Group",
        "CIO",
        "Charitable Incorporated Organisation",
    )

    charity_causes = (
        "Animal Welfare",
        "Arts and Culture",
        "Children",
        "Community",
        "Crime and Justice",
        "Disability",
        "Disaster Relief",
        "Education",
        "Environment",
        "Health",
        "Human Rights",
        "International Development",
        "Justice",
        "Mental Health",
        "Poverty",
        "Religion",
        "Social Services",
    )

    def charity_type(self):
        return "Demonstration Charity"

    def company_number(self):
        return self.numerify("XX00####")

    def charity_name(self):
        return "{} {} {}".format(
            self.address.city(),
            self.random_element(self.charity_causes),
            self.random_element(self.charity_suffixes),
        )

    def charity_area_of_benefit(self):
        fake_city = self.address.city().replace(" ", "").upper()
        fake_country = self.address.country()
        possible_areas = [
            "NOT DEFINED",
            "SEE OBJECTS",
            fake_city,
            "PARISH OF {}".format(fake_city),
            "{}.".format(fake_city),
            "ANCIENT PARISH OF {}".format(fake_city),
            "COUNTY AND CITY OF {}".format(fake_city),
            "NATIONAL",
            "NATIONAL AND OVERSEAS",
            "{} AND {}".format(fake_city, self.address.city().upper()),
            "NATIONAL",
            "NOT DEFINED.",
            "UNDEFINED. IN PRACTICE, LOCAL.",
            "SEE OBJECTS",
            "UNDEFINED. IN PRACTICE, LOCAL",
            "LOCAL",
            "WORLDWIDE",
            "NATIONAL AND OVERSEAS",
            "UNITED KINGDOM",
            "IN PRACTICE THE CATCHMENT AREA OF THE SCHOOL",
            "OVERSEAS",
            "UNDEFINED. IN PRACTICE, NATIONAL",
            "GREATER LONDON",
            "UNRESTRICTED",
            "SEE OBJECT",
            "UNDEFINED",
            "LONDON",
            "CITY OF BIRMINGHAM",
            "UNDEFINED. IN PRACTICE, NATIONAL.",
            "CATCHMENT AREA OF THE SCHOOL",
            "UNDEFINED. IN PRACTICE, NATIONAL AND OVERSEAS.",
            "ENGLAND AND WALES",
            fake_country.upper(),
            "UK AND {}".format(fake_country.upper()),
        ]
        return self.random_element(possible_areas)

    def charity_governing_document(self):
        paragraph = self.generator.sentence()
        possible_gd = [
            "AMALGAMATED",
            "MODEL CONSTITUTION AND RULES (ALREADY LODGED)",
            "PAROCHIAL CHURCH COUNCIL POWERS MEASURE (1956) AS AMENDED AND CHURCH REPRESENTATION RULES",
            "Amalgamated",
            "SEE INDIVIDUAL CONSTITUENTS",
            "UNKNOWN",
            "MODEL CONSTITUTION AND RULES",
            "ROYAL CHARTER 1925",
            "ROYAL CHARTER GRANTED 4 JANUARY 1912",
            "PAROCHIAL CHURCH COUNCIL POWERS MEASURE (1956) AS AMENDED AND CHURCH REPRESENTATION RULES THAT CAME INTO FORCE ON 02 JAN 1957",
            "ROYAL CHARTER 4TH JANUARY 1912",
            "ROYAL CHARTER 4 JANUARY 1912",
            "MODEL CONSTITUTION AND RULES ALREADY LODGED",
            "CONSTITUTION AND RULES ALREADY LODGED",
            "DEED OF UNION (1932) AND METHODIST CHURCH ACT (1976)",
            "CONSTITUTION",
            "SEA CADET REGULATIONS",
            "ROYAL CHARTER GRANTED 04/01/1912",
            "ROYAL CHARTER DATED 4TH JANUARY 1912",
            "ROYAL CHARTER 1925.",
            "Scheme dated 29 October 2014",
            "DECLARATION OF TRUST DATED 22/11/96",
            "ROYAL CHARTER GRANTED 14 DECEMBER 1922",
            "SEE RAFA CORPORATE BODY 226686",
            "ROYAL CHARTER 14 DECEMBER 1922",
            "CONSTITUTION ADOPTED 01 DEC 2017",
            "SCHEME OF THE HIGH COURT OF JUSTICE (CHANCERY DIVISION) OF 21 APRIL 1958",
            "CONSTITUTION AND RULES",
            "ROYAL CHARTER 14TH DECEMBER 1922",
            "Scheme dated 22 May 2015",
            "ROYAL CHARTER GRANTED 26 JUNE 1996 AS AMENDED BY SCHEME DATED 28 MAY 1997",
            "ROYAL CHARTER GRANTED 4TH JANUARY 1912",
            "ROYAL CHARTER GRANTED 04 JAN 1912",
            "NO FORMAL TRUST INSTRUMENT",
            "ROYAL CHARTER OF 1925",
            "SUPPLEMENTAL ROYAL CHARTER AND RULES AND BYE LAWS OF THE RNA (266982)",
            "ROYAL CHARTER DATED 4 JANUARY 1912",
            "SCHEME OF THE CHARITY COMMISSION 2 AUGUST 2016",
            "DECLARATION OF TRUST DATED 27/03/1997",
            "MODEL CONSTITUTION AND RULES(ALREADY LODGED)",
            "ROYAL CHARTER - 4TH JANUARY 1912",
            "THE MODEL CONSTITUTION WAS APPROVED ON 17 OCTOBER 1996 AND ADOPTED WITHOUT ANY AMENDMENT BY THE CHARITY ON 29 MAY 1997.",
            "CONSTITUTION ADOPTED 29 MAY 1997",
            "SEE INDIVIDUAL CONSTITUENTS.",
            "RULES",
            "Memorandum",
            "Constitution",
            "PAROCHIAL CHURCH COUNCIL POWERS MEASURE (1956) AS AMENDED AND CHURCH REPRESENTATION RULES THAT CAME INTO FORCE ON 02 JAN 1956",
            "TrustDeed",
            "THE MODEL CONSTITUTION WAS APPROVED ON 17 OCTOBER 1996 AND ADOPTED WITHOUT ANY AMENDMENT BY THE CHARITY ON 29TH MAY, 1997.",
            "ROYAL CHARTER GRANTED 26 JUNE 1996 AS AMENDED BY SCHEME DATED 28 MAY 1997.",
            "CONSTITUTION AND STANDARD BRANCH RULES APPROVED ON 26 JANUARY 2008",
            "DECLARATION OF TRUST DATED 31/01/1997 AS AMENDED BY SUPPLEMENTAL DEED DATED 1 NOVEMBER 2007",
            "Scheme dated 29 Feb 2016",
        ] + [paragraph * 20]
        return self.random_element(possible_gd)
