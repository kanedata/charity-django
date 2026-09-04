from django.test import TestCase

from charity_django.postcodes.models import GeoCode


class TestGeoCodes(TestCase):
    def setUp(self):
        GeoCode.objects.create(GEOGCD="TEST123", GEOGNM="Test Area")
        GeoCode.objects.create(GEOGCD="TESTABC", GEOGNM="Test Area", PARENTCD="TEST123")
        GeoCode.objects.create(GEOGCD="TESTDEF", GEOGNM="Test Area", PARENTCD="TEST123")
        GeoCode.objects.create(GEOGCD="TESTGHI", GEOGNM="Test Area", PARENTCD="TESTABC")

    def test_geocode_creation(self):
        geocode = GeoCode.objects.get(GEOGCD="TEST123")
        self.assertEqual(geocode.GEOGNM, "Test Area")

    def test_geocode_parent(self):
        geocode = GeoCode.objects.get(GEOGCD="TESTABC")
        self.assertEqual(geocode.parent.GEOGCD, "TEST123")

    def test_geocode_get_parents(self):
        geocode = GeoCode.objects.get(GEOGCD="TESTGHI")
        parents = geocode.get_parents()
        self.assertEqual([parent.GEOGCD for parent in parents], ["TESTABC", "TEST123"])

    def test_geocode_get_children(self):
        geocode = GeoCode.objects.get(GEOGCD="TEST123")
        children = geocode.get_children()
        self.assertEqual([child.GEOGCD for child in children], ["TESTABC", "TESTDEF"])

    def test_geocode_get_siblings(self):
        geocode = GeoCode.objects.get(GEOGCD="TESTDEF")
        siblings = geocode.get_siblings()
        self.assertEqual([sibling.GEOGCD for sibling in siblings], ["TESTABC"])

    def test_geocode_no_parent(self):
        geocode = GeoCode.objects.get(GEOGCD="TEST123")
        self.assertIsNone(geocode.parent)

    def test_geocode_parent_incorrect(self):
        geocode = GeoCode.objects.get(GEOGCD="TEST123")
        geocode.PARENTCD = "INCORRECT"
        geocode.save()
        geocode.refresh_from_db()
        self.assertIsNone(geocode.parent)
