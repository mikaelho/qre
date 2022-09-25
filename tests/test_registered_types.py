import datetime
from decimal import Decimal
from uuid import UUID

import pytest

import qre


@pytest.mark.parametrize(
    "inp, result",
    (
        ("123", {"num": 123}),
        ("-123", {"num": -123}),
        ("+123", {"num": 123}),
        ("+000123", {"num": 123}),
        ("0123", {"num": 123}),
        ("-123.0", {}),
    ),
)
def test_type_int(inp, result):
    m = qre.Matcher("[num:int]")
    assert m.match(inp) == result


@pytest.mark.parametrize(
    "inp, result",
    (
        ("123.4", {"num": 123.4}),
        ("-123.4", {"num": -123.4}),
        ("+123.4", {"num": 123.4}),
        ("+000123.4", {"num": 123.4}),
        ("-123.0", {"num": -123.0}),
    ),
)
def test_type_float(inp, result):
    m = qre.Matcher("[num:float]")
    assert m.match(inp) == result


@pytest.mark.parametrize(
    "inp, result",
    (
        ("123.4", {"num": Decimal("123.4")}),
        ("-123.4", {"num": Decimal("-123.4")}),
        ("+123.4", {"num": Decimal("123.4")}),
        ("+000123.4", {"num": Decimal("123.4")}),
        ("-123.0", {"num": Decimal("-123")}),
        ("-.1", {"num": Decimal("-0.1")}),
    ),
)
def test_type_decimal(inp, result):
    m = qre.Matcher("[num:decimal]")
    assert m.match(inp) == result


@pytest.mark.parametrize(
    "inp, result",
    (
        ("d4d42dd9-68de-463d-b43e-b1a12a7623d3", {"uuid": UUID("d4d42dd968de463db43eb1a12a7623d3")}),
        ("d4d42dd968de463db43eb1a12a7623d3", {"uuid": UUID("d4d42dd968de463db43eb1a12a7623d3")}),
        ("d4d42dd968de463db43eb1a12a7623", {}),
    ),
)
def test_type_uuid(inp, result):
    m = qre.Matcher("[uuid:uuid]")
    assert m.match(inp) == result


def test_type_date():
    m = qre.Matcher("[date:date]")
    assert m.match("2022-09-16") == {"date": datetime.date(2022, 9, 16)}


def test_type_datetime__naive():
    now = datetime.datetime.utcnow()
    as_str = now.isoformat()

    m = qre.Matcher("[datetime:datetime]")
    assert m.match(as_str) == {"datetime": now}


def test_type_datetime__with_timezone():
    m = qre.Matcher("[datetime:datetime]")
    as_datetime = m.match("2007-11-20 22:19:17+02:00")["datetime"]

    assert as_datetime.year == 2007
    assert as_datetime.second == 17
    assert as_datetime.tzinfo == datetime.timezone(datetime.timedelta(seconds=7200))


@pytest.mark.parametrize(
    "inp, result",
    (
        ("abcf123", {"chars": "abcf"}),
        ("abcf123#", {"chars": "abcf"}),
        ("ACBAAC_123", {"chars": "ACBAAC"}),
    ),
)
def test_type_letter(inp, result):
    m = qre.Matcher("[chars:letters]*")
    assert m.match(inp) == result


@pytest.mark.parametrize(
    "inp, result",
    (
        ("abcf123", {"chars": "abcf123"}),
        ("abcf123#", {"chars": "abcf123"}),
        ("ACBAAC_123", {"chars": "ACBAAC_123"}),
    ),
)
def test_type_identifier(inp, result):
    m = qre.Matcher("[chars:identifier]*")
    assert m.match(inp) == result


@pytest.mark.parametrize(
    "string, result",
    (
        ("(a)", True),
        ("{a}", True),
        ("[[a]]", True),
        ("[[a)", True),
        ("(a", False),
        ("a}", False),
    ),
)
def test_type_open_and_close(string, result):
    m = qre.Matcher("[:open]+[:close]")
    print(m.match(string).unnamed)
    assert bool(m.match(string)) == result

@pytest.mark.parametrize(
    "string",
    (
        "john@doe.com",
        "dotted.name@dotted.domain.org",
        "ug.ly-name_1@ug-ly.domain0.co.uk",
        "ínternatiönal@world.net",
    ),
)
def test_type_email(string):
    matcher = qre.Matcher("[email:email]")
    assert matcher.match(string) == {"email": string}


@pytest.mark.parametrize(
    "inp, result",
    (
        ("127.0.0.1", {"ip": "127.0.0.1"}),
        ("192.168.1.1", {"ip": "192.168.1.1"}),
        ("127.0.0.1", {"ip": "127.0.0.1"}),
        ("0.0.0.0", {"ip": "0.0.0.0"}),
        ("255.255.255.255", {"ip": "255.255.255.255"}),
        ("256.256.256.256", {}),
        ("999.999.999.999", {}),
        ("1.2.3", {}),
        ("1.2.3.4", {"ip": "1.2.3.4"}),
    ),
)
def test_type_ipv4(inp, result):
    m = qre.Matcher("[ip:ipv4]")
    assert m.match(inp) == result


@pytest.mark.parametrize(
    "inp, result",
    (
        ("4569403961014710", {"card": "4569403961014710"}),
        ("5191914942157165", {"card": "5191914942157165"}),
        ("370341378581367", {"card": "370341378581367"}),
        ("38520000023237", {"card": "38520000023237"}),
        ("6011000000000000", {"card": "6011000000000000"}),
        ("3566002020360505", {"card": "3566002020360505"}),
        ("1234566660000222", {}),
    ),
)
def test_type_creditcard(inp, result):
    m = qre.Matcher("[card:creditcard]")
    assert m.match(inp) == result


@pytest.mark.parametrize(
    "inp, is_url",
    (
        ("abcdef", False),
        ("www.whatever.com", False),
        ("https://github.com/geongeorge/i-hate-regex", True),
        ("https://www.facebook.com/", True),
        ("https://www.google.com/", True),
        ("https://xkcd.com/2293/", True),
        ("https://this-shouldn't.match@example.com", False),
        ("http://www.example.com/", True),
    ),
)
def test_type_url(inp, is_url):
    m = qre.Matcher("[url:url]")
    assert bool(m.match(inp)) == is_url
