import re

import titlecase

VOWELS = re.compile("[AEIOUYaeiouy]")
ORD_NUMBERS_RE = re.compile(r"([0-9]+(?:st|nd|rd|th))")
SENTENCE_SPLIT = re.compile(r"(\. )")


def title_exceptions(word, **kwargs):
    word_test = word.strip("(){}<>.")

    # lowercase words
    if word_test.lower() in ["a", "an", "of", "the", "is", "or"]:
        return word.lower()

    # uppercase words
    if word_test.upper() in [
        "UK",
        "FM",
        "YMCA",
        "PTA",
        "PTFA",
        "NHS",
        "CIO",
        "U3A",
        "RAF",
        "PFA",
        "ADHD",
        "I",
        "II",
        "III",
        "IV",
        "V",
        "VI",
        "VII",
        "VIII",
        "IX",
        "X",
        "XI",
        "AFC",
        "CE",
        "CIC",
    ]:
        return word.upper()

    # words with no vowels that aren't all uppercase
    if word_test.lower() in [
        "st",
        "mr",
        "mrs",
        "ms",
        "ltd",
        "dr",
        "cwm",
        "clwb",
        "drs",
    ]:
        return word_test.title()

    # words with number ordinals
    if bool(ORD_NUMBERS_RE.search(word_test.lower())):
        return word.lower()

    # words with dots/etc in the middle
    for s in [".", "'", ")"]:
        dots = word.split(s)
        if len(dots) > 1:
            # check for possesive apostrophes
            if s == "'" and dots[-1].upper() == "S":
                return s.join(
                    [
                        titlecase.titlecase(i, callback=title_exceptions)
                        for i in dots[:-1]
                    ]
                    + [dots[-1].lower()]
                )
            # check for you're and other contractions
            if word_test.upper() in ["YOU'RE", "DON'T", "HAVEN'T"]:
                return s.join(
                    [
                        titlecase.titlecase(i, callback=title_exceptions)
                        for i in dots[:-1]
                    ]
                    + [dots[-1].lower()]
                )
            return s.join(
                [titlecase.titlecase(i, callback=title_exceptions) for i in dots]
            )

    # words with no vowels in (treat as acronyms)
    if not bool(VOWELS.search(word_test)):
        return word.upper()

    return None


def to_titlecase(s, sentence=False):
    if not isinstance(s, str):
        return s

    s = s.strip()

    # if it contains any lowercase letters then return as is
    if not s.isupper() and not s.islower():
        return s

    # if it's a sentence then use capitalize
    if sentence:
        return "".join([sent.capitalize() for sent in re.split(SENTENCE_SPLIT, s)])

    # try titlecasing
    s = titlecase.titlecase(s, callback=title_exceptions)

    # Make sure first letter is capitalise
    return s[0].upper() + s[1:]


def regex_search(s, regex):
    return re.search(regex, s) is not None


def list_to_string(items, sep=", ", final_sep=" and "):
    if isinstance(items, str):
        return items
    if isinstance(items, set):
        items = list(items)

    if len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return final_sep.join(items)
    else:
        return sep.join(items[0:-1]) + final_sep + items[-1]


def clean_url(url):
    if not url:
        return None
    url = re.sub(r"(https?:)?//", "", url)
    if url.startswith("www."):
        url = url[4:]
    if url.endswith("/"):
        url = url[:-1]
    return url


def working_url(url):
    if not url:
        return None
    if url.startswith("http") and not url.startswith("//"):
        return url
    return "https://" + url
