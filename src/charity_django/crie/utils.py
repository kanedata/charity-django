import re
from typing import Generator


def parse_classification(value: str) -> Generator[str, None, None]:
    classifications = (
        value.replace(
            ". The following classification is not of lesser importance than the one listed above: ",
            ";;;",
        )
        .replace(
            ". The following classification is of lesser importance than the one listed above: ",
            ";;;",
        )
        .split(";;;")
    )

    def process_buffer(value: str):
        return value.strip().replace(" / ", "/")

    for i, c in enumerate(classifications):
        buffer = ""
        bracket_level = 0
        for char in c:
            if char in ["[", "("]:
                bracket_level += 1
                if buffer.strip() and bracket_level <= 2:
                    yield process_buffer(buffer)
                    buffer = ""
                if bracket_level > 2:
                    buffer += char
            elif char in ["]", ")"]:
                if buffer.strip() and bracket_level <= 2:
                    yield process_buffer(buffer)
                    buffer = ""
                if bracket_level > 2:
                    buffer += char
                bracket_level -= 1
            elif char == ";":
                if buffer.strip():
                    yield process_buffer(buffer)
                buffer = ""
            else:
                buffer += char
        if buffer.strip():
            yield process_buffer(buffer)


def parse_classification_simple(value: str) -> Generator[str, None, None]:
    classification = set(value.split(";"))
    for c in classification:
        c = c.strip("\"', ")
        if c:
            yield c


ENGLISH_PHRASES = [
    re.compile(rf"\b{word.lower()}\b", re.IGNORECASE)
    for word in [
        "the",
        "limited",
        "and",
        "of",
        "charity",
        "company",
        "guarantee",
        "association",
        "foundation",
        "housing",
        "school",
        "blood",
        "scout",
        "group",
        "development",
        "ltd",
        "community",
        "playgroup",
        "residential",
        "enterprise",
        "center",
        "resource",
        "choir",
        "festival",
        "music",
        "staff",
        "fund",
        "college",
        "theatre",
        "healthcare",
        "social",
        "inclusion",
        "ministries",
        "ireland",
    ]
]


def detect_language(text: str) -> str:
    """A very basic language detection based on character frequency."""
    text = text.lower()
    irish_chars = sum(text.count(c) for c in "áéíóúÁÉÍÓÚ")
    english_count = 0
    for phrase in ENGLISH_PHRASES:
        if phrase.search(text):
            english_count += 1
    if irish_chars and not english_count:
        return "ga"
    return "en"
