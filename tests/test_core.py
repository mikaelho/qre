import datetime

import pytest

from qre import qre


def test_readme_example_opener():
    assert qre("He* [planet]!").match("Hello World!") == {"planet": "World"}
    assert qre("It* [temp:float]?°C *").match("It's -10.2 °C outside!") == {"temp": -10.2}


def test_readme_example_basic_usage():
    matcher = qre("Invoice+*[year:4]+[month:2]+[day:2].pdf")
    assert matcher.match("Invoice_RE2321_2021_01_15.pdf") == {"year": "2021", "month": "01", "day": "15"}
    assert matcher.match("Invoice RE2321 2021-01-15.pdf") == {"year": "2021", "month": "01", "day": "15"}

    matcher_with_type = qre("Invoice+*[date:date].pdf")
    assert matcher_with_type.match("Invoice RE2321 2021-01-15.pdf") == {"date": datetime.date(2021, 1, 15)}

    assert qre("ABC-[value:int]").match("ABC-13")


def test_readme_example_typehints():
    matcher = qre("[year:int]-[month:int]: [value:float]")
    assert matcher.match("2021-01: -12.786") == {
        "year": 2021,
        "month": 1,
        "value": -12.786,
    }
    assert not matcher.match("2021-01-abc: Hello")
    assert matcher.match("1234-01: 123.123")
    assert (
        matcher.regex
        == "(?P<year>[+-]?[0-9]+)\\-(?P<month>[+-]?[0-9]+):\\ (?P<value>[+-]?(?:[0-9]*[.])?[0-9]+)"
    )
    assert matcher.converters == {"year": int, "month": int, "value": float}

@pytest.mark.parametrize(
    "matcher, string, is_match",
    (
        ("match", "hit", True),
        ("match", "hit miss", False),
        ("match_start", "hit miss", True),
        ("match_start", "miss hit", False),
        ("match_end", "miss hit", True),
        ("match_end", "hit miss", False),
        ("search", "miss hit miss", True),
        ("search", "miss", False),
    )
)
def test_functions(matcher, string, is_match):
    pattern = "hit"
    assert bool(getattr(qre(pattern), matcher)(string)) == is_match


def test_search_all():
    matcher = qre("nugget")
    assert matcher.search_all("There is a nugget of information")

    matcher = qre("no nugget")
    assert not matcher.search_all("Can't find any nuggets of information")

    matcher = qre("nuggets")
    assert len(matcher.search_all("There are nuggets and nuggets of information")) == 2

    matcher = qre("[:letters]")
    assert [result.unnamed for result in matcher.search_all("Many hits here")] == [['Many'], ['hits'], ['here']]


@pytest.mark.parametrize(
    "pattern, string, result",
    (
        # Wildcards
        ("*.py", "hello.py", True),
        ("*.zip", "hello.py", False),
        ("++.py", "yo.py", True),
        ("+++.py", "yo.py", False),
        ("yo???.py", "yo12.py", True),
        ("yo???.py", "yo1234.py", False),
        # Either
        ("a|b", "a", True),
        ("a|b", "c", False),
        ("[:int]|[:float]", "1", True),
        ("[:int]|[:float]", "1.0", True),
        # Wildcards and either escaped
        ("[[brackets]]", "[brackets]", True),
        ("real[*]times", "real*times", True),
        ("real[*]times", "real+times", False),
        ("real[+]plus", "real+plus", True),
        ("real[+]plus", "real-plus", False),
        ("real[?]question mark", "real?question mark", True),
        ("real[?]question mark", "real!question mark", False),
        ("real[|]pipe", "real|pipe", True),
        ("real[|]pipe", "real!pipe", False),
        ("[[|(", "[", True),
        ("[[|(", "(", True),
        # Groups
        ("[file].py", "hello.py", True),
        ("[file].zip", "hello.py", False),
        ("[folder]/[filename].js", "foo/bar.js", True),
        ("*.[extension]", "/root/folder/file.exe", True),
        ("[folder]/[filename].[extension]", "test/123.pdf", True),
        ("[]/[filename][?][]", "www.site.com/home/hello.js?p=1", True),
        # Groups with width
        ("[:4][:2]", "123456", True),
        ("[:4][:2]", "12345", False),
        ("[a:4][b:2]", "123456", True),
        ("[a:4][b:2]", "12345", False),
        # Unicode
        ("*.p?", "whatevör.pü", True),
        ("*.[:letters]", "whatevör.pü", True),
        ("*.[:letters]", "whatevör.p¥", False),
    ),
)
def test_match_patterns(pattern, string, result):
    assert bool(qre(pattern).match(string)) == result


@pytest.mark.parametrize(
    "pattern, string, test_result, match_result",
    (
        ("*.py", "hello.py", True, []),
        ("[].py", "hello.py", True, ["hello"]),
        ("*.py", "hello.__", False, []),
        ("[].py", "hello.__", False, []),
    ),
)
def test_result(pattern, string, test_result, match_result):
    assert bool(qre(pattern).match(string)) == test_result
    assert qre(pattern).match(string).unnamed == match_result


def test_unnamed_wildcards():
    assert qre("[] sees []").match("Tim sees Jacob").unnamed == ["Tim", "Jacob"]


def test_match_dict_with_named_groups_and_hints():
    assert qre("[folder]/[file_name][file_id: int].py").match("home/hello1.py") == {
        "folder": "home",
        "file_name": "hello",
        "file_id": 1,
    }


def test_match_with_widths():
    assert qre("[a:2][b:3]").match("12345") == {"a": "12", "b": "345"}
    assert qre("[:2][:3]").match("12345").unnamed == ["12", "345"]


def test_return_falsy_if_no_match():
    assert not qre("[folder]/[filename][?][params]").match("hello.js?p=1")


def test_return_value_as_object():
    result = qre("[name:letters] is []").match("Tim is a boy").as_object()
    assert result.name == "Tim"
    assert result.unnamed == ["a boy"]
    assert result


def test_return_value_as_object__no_match():
    result = qre("[name:letters] is []").match("Tim is").as_object()
    assert not result


def test_match_when_regex_values():
    assert qre("[folder]/[filename][?][params]").match("home/hello.js?p=1") == dict(
        folder="home", filename="hello.js", params="p=1"
    )


def test_match_wildcards():
    assert qre("*/[filename]+js").match("home/hello.js") == dict(filename="hello")


def test_save_unnamed_groups():
    result = qre("[]/[filename][?][]").match("www.site.com/home/hello.js?p=1")
    assert result == {"filename": "hello.js"}
    assert result.unnamed == ["www.site.com/home", "p=1"]


def test_unnamed_groups_with_hints():
    assert qre("[:int] [:float] [:int]").match("1 2.3 4").unnamed == [1, 2.3, 4]


def test_mixed_groups_with_hints():
    result = qre("[one:int] [:int]").match("1 2")

    assert result == {"one": 1}
    assert result.unnamed == [2]
    assert list(result.all_values()) == [2, 1]
    assert list(result.all_items()) == [(None, 2), ("one", 1)]


def test_case_sensitive():
    assert qre("Hello []").match("Hello World")
    assert not qre("hello []").match("Hello World")

    assert qre("Hello []", case_sensitive=False).match("Hello World")
    assert qre("hello []", case_sensitive=False).match("Hello World")

    # keep capture group names
    assert qre("HELLO [PlAnEt]", case_sensitive=False).match("Hello Earth") == {
        "PlAnEt": "Earth"
    }


def test_patterns_search():
    matcher = qre("One", "Three")
    assert not matcher.search("Two")
    assert matcher.search("One Two")
    assert matcher.search("One Two Three")


def test_patterns_search_strict():
    matcher = qre("One", "Three", strict=True)
    assert not matcher.search("Two")
    assert not matcher.search("One Two")  # strict: All or nothing
    assert matcher.search("One Two Three")


def test_patterns_search__named():
    matcher = qre("Key [key:letters]", "Value [value:int]")
    assert matcher.search("Key A") == {"key": "A"}
    assert matcher.search("Key A, Value 1") == {"key": "A", "value": 1}


def test_patterns_search__named__strict():
    matcher = qre("Key [key:letters]", "Value [value:int]", strict=True)
    assert matcher.search("Key A") == {}  # strict: All or nothing
    assert matcher.search("Key A, Value 1") == {"key": "A", "value": 1}


def test_patterns_search__unnamed():
    matcher = qre("Key [:letters]", "Value [:int]")
    assert matcher.search("Key A").unnamed == ["A"]
    assert matcher.search("Key A, Value 1").unnamed == ["A", 1]


def test_patterns_search__unnamed__strict():
    matcher = qre("Key [:letters]", "Value [:int]", strict=True)
    assert matcher.search("Key A").unnamed == []  # strict: All or nothing
    assert matcher.search("Key A, Value 1").unnamed == ["A", 1]


def test_patterns_overlapping_group_names():
    matcher = qre("[value:int]", "[value:letters]")
    assert matcher.match("1") == {"value": 1}
    assert matcher.match("A") == {"value": "A"}
