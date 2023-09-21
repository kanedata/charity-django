from unittest import TestCase

from charity_django.utils.orgid import (
    Orgid,
    OrgidField,
)


class TestUtilsOrgid(TestCase):
    def test_create_orgid(self):
        orgid = Orgid("GB-CHC-123456")
        self.assertEqual(orgid.scheme, "GB-CHC")
        self.assertEqual(orgid.id, "123456")
        self.assertEqual(orgid, "GB-CHC-123456")

    def test_create_orgid_withdash(self):
        orgid = Orgid("GB-CHC-123456-ABCDEF")
        self.assertEqual(orgid.scheme, "GB-CHC")
        self.assertEqual(orgid.id, "123456-ABCDEF")
        self.assertEqual(orgid, "GB-CHC-123456-ABCDEF")

    def test_360g_orgid(self):
        orgid = Orgid("360G-123456")
        self.assertEqual(orgid.scheme, "360G")
        self.assertEqual(orgid.id, "123456")
        self.assertEqual(orgid, "360G-123456")

        orgid = Orgid("360G-123456-ABCDEF")
        self.assertEqual(orgid.scheme, "360G")
        self.assertEqual(orgid.id, "123456-ABCDEF")
        self.assertEqual(orgid, "360G-123456-ABCDEF")

    def test_orgid_field(self):
        f = OrgidField()

        for id in [
            "GB-CHC-123456",
            "GB-CHC-123456-ABCDEF",
            "360G-123456",
            "360G-123456-ABCDEF",
        ]:
            self.assertEqual(f.to_python(id), id)
            self.assertEqual(f.from_db_value(id, None, None), id)
            self.assertIsInstance(f.to_python(id), Orgid)
            self.assertIsInstance(f.from_db_value(id, None, None), Orgid)

        self.assertIsNone(f.to_python(None))
        self.assertIsNone(f.from_db_value(None, None, None))
