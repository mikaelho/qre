from dataclasses import dataclass
from decimal import Decimal

from qre import qre, register_type


def test_sample_1():
    assert qre("* pattern").match("First pattern")


def test_sample_2():
    assert qre("World's [] pattern").match("World's coolest pattern").unnamed == ["coolest"]


def test_sample_3():
    assert qre(
        "product id: [product_id], units: [units: int], price: [unit_price: decimal]", case_sensitive=False
    ).match("Product ID: A123, Units: 3, Price: 1.23") == {
        "product_id": "A123", "units": 3, "unit_price": Decimal("1.23")
    }


def test_my_first_match():
    assert qre("in [place]").search("Match made in heaven") == {"place": "heaven"}


def test_unnamed_groups():
    assert qre("[] [:int]").match("Lesson 1").unnamed == ["Lesson", 1]


def test_register_type():
    register_type("mood", r"[😀😞]", lambda emoji: {"😀": "good", "😞": "bad"}.get(emoji, "unknown"))
    assert qre("[mood:mood]").search("I'm feeling 😀 today!") == {"mood": "good"}


def test_matcher():
    matcher = qre("value: [quantitative:float]|[qualitative]", case_sensitive=False)
    assert matcher.match("Value: 1.0") == {"quantitative": 1.0}  # Or any of the other functions above
    assert matcher.regex == "value:\\ (?P<quantitative>[+-]?(?:[0-9]*[.])?[0-9]+)|(?P<qualitative>.*)"
    assert matcher.converters == {'quantitative': float}


def test_use_with_dataclasses():
    @dataclass
    class Order:
        product_id: str
        units: int
        unit_price: Decimal

        @property
        def total_price(self):
            return self.units * self.unit_price

    matcher = qre(
        "product id: [product_id], units: [units: int], price: [unit_price: decimal]", case_sensitive=False
    )

    order = Order(**matcher.match("Product ID: A123, Units: 3, Price: 1.23"))

    assert order.product_id == "A123"
    assert order.units == 3
    assert order.unit_price == Decimal("1.23")
    assert order.total_price == Decimal("3.69")
