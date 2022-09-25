from decimal import Decimal

import qre


def test_sample_1():
    assert qre.match("* pattern", "First pattern")


def test_sample_2():
    assert qre.match(
        "World's [] pattern", "World's coolest pattern"
    ).unnamed == ["coolest"]


def test_sample_3():
    assert qre.match(
        "product id: [product_id], units: [units: int], price: [unit_price: decimal]",
        "Product ID: A123, Units: 3, Price: 1.23",
        case_sensitive=False,
    ) == {"product_id": "A123", "units": 3, "unit_price": Decimal("1.23")}


def test_my_first_match():
    assert qre.search("in [place]", "Match made in heaven") == {"place": "heaven"}


def test_unnamed_groups():
    assert qre.match("[] [:int]", "Lesson 1").unnamed == ["Lesson", 1]


def test_register_type():
    qre.register_type("mood", r"[😀😞]", lambda emoji: {"😀": "good", "😞": "bad"}.get(emoji, "unknown"))
    assert qre.search("[mood:mood]", "I'm feeling 😀 today!") == {"mood": "good"}

def test_matcher():
    matcher = qre.Matcher("value: [quantitative:float]|[qualitative]", case_sensitive=False)
    assert matcher.match("Value: 1.0") == {"quantitative": 1.0}  # Or any of the other functions above
    assert matcher.regex == "value:\\ (?P<quantitative>[+-]?(?:[0-9]*[.])?[0-9]+)|(?P<qualitative>.*)"
    assert matcher.converters == {'quantitative': float}
