from unittest import TestCase

from charity_django.utils.text import (
    clean_url,
    list_to_string,
    regex_search,
    to_titlecase,
    working_url,
)


class TestUtilsText(TestCase):
    def test_regex_search(self):
        self.assertTrue(regex_search("abc", r"abc"))
        self.assertFalse(regex_search("abc", r"def"))
        self.assertTrue(regex_search("test", "test"))
        self.assertTrue(regex_search("1234", "[0-9]+"))
        self.assertFalse(regex_search("test", "1234"))

    def test_list_to_string(self):
        cases = [
            (["a"], "a"),
            (["a", "b"], "a and b"),
            (["a", "b", "c"], "a, b and c"),
            (["a", "b", "c", "d"], "a, b, c and d"),
            ("Blah blah", "Blah blah"),
            ("item1", "item1"),
            (set(["item1"]), "item1"),
            (["item1"], "item1"),
            (["item1", "item2"], "item1 and item2"),
            (["item1", "item2", "item3"], "item1, item2 and item3"),
        ]
        for items, expected in cases:
            self.assertEqual(list_to_string(items), expected)

        self.assertEqual(
            list_to_string(["a", "b", "c", "d"], final_sep=" or "),
            "a, b, c or d",
        )
        self.assertEqual(
            list_to_string(["a", "b", "c", "d"], sep="", final_sep=""),
            "abcd",
        )
        self.assertEqual(
            list_to_string(["a", "b", "c", "d"], sep="|", final_sep="@"),
            "a|b|c@d",
        )
        self.assertIsInstance(list_to_string(set(("a", "b", "c", "d"))), str)

    def test_to_titlecase(self):
        cases = [
            ("", ""),
            ("a", "A"),
            ("a b", "A B"),
            ("a b c", "A B C"),
            ("aB", "aB"),
            ("MRS SMITH", "Mrs Smith"),
            ("MRS SMITH'S", "Mrs Smith's"),
            ("i don't know", "I Don't Know"),
            ("the 1st place", "The 1st Place"),
            ("mr smith", "Mr Smith"),
            # ("mr. smith", "Mr. Smith"),  # currently fails - should work
            ("MR O'TOOLE", "Mr O'Toole"),
            ("TOM OF TABLE CIC", "Tom of Table CIC"),
            (500, 500),
            (None, None),
            ("THE CHARITY THE NAME", "The Charity the Name"),
            ("CHARITY UK LTD", "Charity UK Ltd"),
            ("BCDF", "BCDF"),
            ("MRS SMITH", "Mrs Smith"),
            ("1ST SCOUT GROUP", "1st Scout Group"),
            ("SCOUT 345TH GROUP", "Scout 345th Group"),
            ("THE CHARITY (THE NAME)", "The Charity (the Name)"),
            (12345, 12345),
            ("THE CHARITY (the name)", "THE CHARITY (the name)"),
            ("Charity UK Ltd", "Charity UK Ltd"),
            ("charity uk ltd", "Charity UK Ltd"),
            ("CHARITY'S SHOP UK LTD", "Charity's Shop UK Ltd"),
            ("CHARITY'S YOU'RE SHOP UK LTD", "Charity's You're Shop UK Ltd"),
        ]
        for s, expected in cases:
            self.assertEqual(to_titlecase(s), expected)

        sentences = (
            ("the charity the name", "The charity the name"),
            (
                "the charity the name. another sentence goes here.",
                "The charity the name. Another sentence goes here.",
            ),
            ("you're a silly billy", "You're a silly billy"),
            (
                "you're a silly billy. and so are you.",
                "You're a silly billy. And so are you.",
            ),
        )
        for s, expected in sentences:
            self.assertEqual(to_titlecase(s, sentence=True), expected)

    def test_working_url(self):
        cases = [
            ("https://www.google.com", "https://www.google.com"),
            ("facebook.com", "https://facebook.com"),
            (None, None),
        ]
        for url, expected in cases:
            self.assertEqual(working_url(url), expected)

    def test_clean_url(self):
        cases = [
            ("https://www.google.com", "google.com"),
            ("https://www.google.com/", "google.com"),
            ("facebook.com", "facebook.com"),
            (None, None),
        ]
        for url, expected in cases:
            self.assertEqual(clean_url(url), expected)
