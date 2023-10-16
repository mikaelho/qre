import datetime
from decimal import Decimal
from uuid import UUID

import pytest

from qre import qre


@pytest.mark.parametrize(
    "string, result",
    (
        ("123", {"num": 123}),
        ("-123", {"num": -123}),
        ("+123", {"num": 123}),
        ("+000123", {"num": 123}),
        ("0123", {"num": 123}),
        ("-123.0", {}),
    ),
)
def test_type_int(string, result):
    assert qre("[num:int]").match(string) == result


@pytest.mark.parametrize(
    "string, result",
    (
        ("123.4", {"num": 123.4}),
        ("-123.4", {"num": -123.4}),
        ("+123.4", {"num": 123.4}),
        ("+000123.4", {"num": 123.4}),
        ("-123.0", {"num": -123.0}),
    ),
)
def test_type_float(string, result):
    assert qre("[num:float]").match(string) == result


@pytest.mark.parametrize(
    "string, result",
    (
        ("123.4", {"num": Decimal("123.4")}),
        ("-123.4", {"num": Decimal("-123.4")}),
        ("+123.4", {"num": Decimal("123.4")}),
        ("+000123.4", {"num": Decimal("123.4")}),
        ("-123.0", {"num": Decimal("-123")}),
        ("-.1", {"num": Decimal("-0.1")}),
    ),
)
def test_type_decimal(string, result):
    assert qre("[num:decimal]").match(string) == result


@pytest.mark.parametrize(
    "string, result",
    (
        ("d4d42dd9-68de-463d-b43e-b1a12a7623d3", {"uuid": UUID("d4d42dd968de463db43eb1a12a7623d3")}),
        ("d4d42dd968de463db43eb1a12a7623d3", {"uuid": UUID("d4d42dd968de463db43eb1a12a7623d3")}),
        ("d4d42dd968de463db43eb1a12a7623", {}),
    ),
)
def test_type_uuid(string, result):
    assert qre("[uuid:uuid]").match(string) == result


def test_type_date():
    assert qre("[date:date]").match("2022-09-16") == {"date": datetime.date(2022, 9, 16)}


def test_type_datetime__naive():
    now = datetime.datetime.utcnow()
    as_str = now.isoformat()

    assert qre("[datetime:datetime]").match(as_str) == {"datetime": now}


def test_type_datetime__with_timezone():
    as_datetime = qre("[datetime:datetime]").match("2007-11-20 22:19:17+02:00")["datetime"]

    assert as_datetime.year == 2007
    assert as_datetime.second == 17
    assert as_datetime.tzinfo == datetime.timezone(datetime.timedelta(seconds=7200))


@pytest.mark.parametrize(
    "string, result",
    (
        ("abcf123", {"chars": "abcf"}),
        ("abcf123#", {"chars": "abcf"}),
        ("ACBAAC_123", {"chars": "ACBAAC"}),
    ),
)
def test_type_letter(string, result):
    assert qre("[chars:letters]*").match(string) == result


@pytest.mark.parametrize(
    "string, result",
    (
        ("abcf123", {"chars": "abcf123"}),
        ("abcf123#", {"chars": "abcf123"}),
        ("ACBAAC_123", {"chars": "ACBAAC_123"}),
    ),
)
def test_type_identifier(string, result):
    assert qre("[chars:identifier]*").match(string) == result


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
    assert bool(qre("[:open]+[:close]").match(string)) == result

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
    assert qre("[email:email]").match(string) == {"email": string}


@pytest.mark.parametrize(
    "string, result",
    (
        ("127.0.0.1", {"ip": "127.0.0.1"}),
        ("192.168.1.1", {"ip": "192.168.1.1"}),
        ("127.0.0.1", {"ip": "127.0.0.1"}),
        ("8.8.8.8", {"ip": "8.8.8.8"}),
        ("255.255.255.255", {"ip": "255.255.255.255"}),
        ("256.256.256.256", {}),
        ("999.999.999.999", {}),
        ("1.2.3", {}),
        ("1.2.3.4", {"ip": "1.2.3.4"}),
    ),
)
def test_type_ipv4(string, result):
    assert qre("[ip:ipv4]").match(string) == result


@pytest.mark.parametrize(
    "string, result",
    (
        ("2001:0db8:85a3:08d3:1319:8a2e:0370:7348", {"ip": "2001:0db8:85a3:08d3:1319:8a2e:0370:7348"}),
        ("2001:db8:85a3:8d3:1319:8a2e:370:7348", {"ip": "2001:db8:85a3:8d3:1319:8a2e:370:7348"}),
        ("2001:db8:85a3:8d3:1319:8a2e::", {"ip": "2001:db8:85a3:8d3:1319:8a2e::"}),
        ("fe80::1ff:fe23:4567:890a%eth2", {"ip": "fe80::1ff:fe23:4567:890a%eth2"}),
        ("abcd:ef12:3456::", {"ip": "abcd:ef12:3456::"}),
        ("abcd:efghi:jklm::", {}),
    ),
)
def test_type_ipv6(string, result):
    assert qre("[ip:ipv6]").match(string) == result


@pytest.mark.parametrize(
    "string, result",
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
def test_type_creditcard(string, result):
    assert qre("[card:creditcard]").match(string) == result


@pytest.mark.parametrize(
    "string, is_url",
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
def test_type_url(string, is_url):
    assert bool(qre("[url:url]").match(string)) == is_url
