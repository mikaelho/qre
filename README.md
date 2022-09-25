# qre - like re, but cuter

[![PyPI - Version](https://img.shields.io/pypi/v/qre)](https://pypi.org/project/qre/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![tests](https://github.com/mikaelho/qre/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/mikaelho/qre/actions/workflows/tests.yml)

| Samples |                                                                                 |
|---------|:--------------------------------------------------------------------------------|
| Pattern | `"* pattern"`                                                                   |
| Input   | `"First pattern"`                                                               |
| Result  | 👍🏼                                                                            |
|         |                                                                                 |
| Pattern | `"World's [] pattern"`                                                          |
| Input   | `"World's coolest pattern"`                                                     |
| Result  | `["coolest"]`                                                                   |
|         |                                                                                 |
| Pattern | `"product id: [product_id], units: [units: int], price: [unit_price: decimal]"` |
| Input   | `"Product ID: A123, Units: 3, Price: 1.23"` (case-insensitive)                  |
| Result  | `{"product_id": "A123", "units": 3, "unit_price": Decimal("1.23")}`             |

This package owes everything, including most of the codebase, to Thomas Feldtmann's
[simplematch](https://github.com/tfeldmann/simplematch). All poor design decisions are mine.
See [this collection](https://github.com/mikaelho/python-human-regex) for other alternatives.

_Status_: Comprehensively tested but never used for anything real. All evolution is expected to be
incremental.

## Quick start

`pip install qre`

My first little match:

```python
import qre

assert qre.search("in [place]", "Match made in heaven") == {"place": "heaven"}
```

`qre` is mostly focused on collecting named groups from the input strings, so the return value is
an easy-to-access dict. Groups are denoted with brackets, which means that patterns are friendly
with f-strings.

For unnamed groups the returned object has been tweaked a little bit - they can be found as a list
in the `unnamed` attribute:

```python
assert qre.match("[] [:int]", "Lesson 1").unnamed == ["Lesson", 1]
```

Type specifiers can be used with both named and unnamed groups. They act both as specs for the
pattern to find and, when applicable, as converters to the right type.

Currently available types are:
- `int`
- `float`
- `decimal`
- `date` (ISO)
- `datetime` (ISO)
- `uuid`
- `letters`
- `identifier` (`letters` plus numbers and underscore)
- `email`
- `url`
- `ipv4`
- `ipv6`
- `creditcard`
- `open` (any one of `(`, `[`, `{`)
- `close` (`)`, `]`, or `}`)

You can register your own types and conversions with `register_type(name, regex, converter=str)`.
As `qre`'s goal is not to replicate the functionality of re, this can also act as the "escape hatch"
when you need just a little bit more than what `qre` offers.

Here's how to use `register_type` to turn an emoji into a textual description:

```python
qre.register_type("mood", r"[😀😞]", lambda emoji: {"😀": "good", "😞": "bad"}.get(emoji, "unknown"))

assert qre.search("[mood:mood]", "I'm feeling 😀 today!") == {"mood": "good" }
```

Note that `register_type` manipulates a global object, so you only need to register custom types
once, probably somewhere towards the start of your program.

PRs for generally useful types are highly welcome.

## Matching functions

Matching functions expect a `pattern` and a `string` to match against. The optional
`case_sensitive` argument is true by default.

- `match` - Match `pattern` against the whole of the `string`
- `match_start` - Match `pattern` against the beginning of the `string`
- `match_end` - Match `pattern` against the end of the `string`
- `search` - Return the first match of the `pattern` in the `string`
- `search_all` - Return all matches of the `pattern` in the `string` as a list

All of the functions always return an object that is either truthy or falsy depending on whether
there was a match or not. They never return `None`, and the `unnamed` attribute contains at least an 
empty list, so the returned object is always safe to iterate.

Alternatively, you can use the Matcher object. It has the following useful attributes:
- `regex` for debugging the generated regex, or for copying it for use with plain `re`
- `converters` for debugging the converters in use

```python
matcher = qre.Matcher("value: [quantitative:float]|[qualitative]", case_sensitive=False)
assert matcher.match("Value: 1.0") == {"quantitative": 1.0}  # Or any of the other functions above
assert matcher.regex == "value:\\ (?P<quantitative>[+-]?(?:[0-9]*[.])?[0-9]+)|(?P<qualitative>.*)"
assert matcher.converters == {'quantitative': float}
```

As a final usage scenario, you can call `qre` on the command line:

```
$ python qre.py
usage: qre.py [-h] [--regex] pattern string
```

## Pattern syntax summary

- Wildcards:
  - `*` - any character 0+ times
  - `+` - any 1 character
  - `?` - any 1 character, maybe
- Operators:
  - `|` - either of two characters or groups
- Groups:
  - `[name]` - named group called "name", returned in the main dict.
  - `[]` - unnamed group, returned in the `unnamed` list
  - `[name:4]`, `[:4]` - group that is 4 characters wide
  - `[name:int]`, `[:int]` - group that matches the type and is converted to that Python type
- Escaping:
  - `[*]`, `[+]`, `[?]`, `[|]` - literal symbol, not wildcard
  - `[[`, `]]` - literal brackets, not groups
