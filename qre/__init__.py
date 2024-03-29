#!/usr/bin/env python3
"""
Pattern syntax summary

Wildcards:
  - * - any character, 0+ times
  - + - any character, exactly once
  - ? - any character, 0-1 times

Operators:
  - | - either of two characters or groups

Groups:
  - [name] - named group called "name", returned in the main dict.
  - [] - unnamed group, returned in the `unnamed` list
  - [name:4]`, `[:4] - group that is 4 characters wide
  - [name:int], [:int] - group that matches the type and is converted to that Python type

Escaping:
  - [*], [+], [?], [|] - literal symbol, not wildcard
  - [[, ]] - literal brackets, not groups
"""

__version__ = "2023.10.1"

import itertools
import re
from types import SimpleNamespace
from typing import Iterable
from typing import List

from qre.registered_types import register_type
from qre.registered_types import registered_types

__all__ = ["register_type", "Matcher", "match", "match_start", "match_end", "search", "search_all"]


# taken from the stdlib re module - minus "*+?[]", because that's our own syntax
SPECIAL_CHARS = {character: "\\" + chr(character) for character in b"(){}-^$\\.&~# \t\n\r\v\f"}


def qre(*patterns, case_sensitive: bool = True, flexible_spaces: bool = True, strict: bool = False):
    if not patterns:
        return ValueError("Must provide at least one pattern")
    elif len(patterns) == 1:
        return Matcher(patterns[0], case_sensitive=case_sensitive, flexible_spaces=flexible_spaces)
    else:
        return MultiMatcher(patterns, case_sensitive=case_sensitive, flexible_spaces=flexible_spaces, strict=strict)


class MatchResult(dict):

    unnamed: list
    _matches: list[re.Match]

    def __bool__(self):
        return bool(self._matches)

    def all_values(self) -> Iterable:
        return itertools.chain(self.unnamed, self.values())

    def all_items(self) -> Iterable[tuple]:
        return itertools.chain(((None, value) for value in self.unnamed), self.items())

    def as_object(self):
        return MatchObject(**self, unnamed=self.unnamed, _matches=self._matches)

    def replace(self, *with_values):
        """
        Replace matched groups, in order, with the given values.

        Unnamed and named groups are treated identically here.
        """
        if not with_values:
            raise ValueError("Provide one or many strings, a list or a dict of replacement values")
        if not self:
            raise ValueError("replace() can only be used on successful match")
        original_string = self._matches[0].string  # All matches have the same matched string

        if len(with_values) == 1:
            if type(with_values[0]) in (tuple, list):
                with_values = with_values[0]

            elif isinstance(with_values[0], dict):
                replacement_values = with_values[0]
                spans = []
                for name in replacement_values:
                    for match in self._matches:
                        try:
                            if match.start(name) != -1:
                                spans.append((*match.span(name), replacement_values[name]))
                        except IndexError:  # Expected: Not all sub-matches have all replacement groups
                            pass
                spans.sort()
                return self._string_with_replacements(original_string, spans)

        if type(with_values) in (tuple, list):
            return self._replace_as_long_as_values_last(original_string, iter(with_values))

    def _replace_as_long_as_values_last(self, original_string, values):
        # Replace all types of groups in order
        # For multi-matches, order of sub-patterns is expected to match the replacement value order
        spans = []
        try:
            for match in self._matches:
                for i in range(match.lastindex):
                    spans.append((*match.span(i + 1), next(values)))
        except StopIteration:
            pass
        spans.sort()
        return self._string_with_replacements(original_string, spans)

    @staticmethod
    def _string_with_replacements(original_string, spans):
        result_string = ""
        previous_end = 0
        for start, end, replacement_value in spans:
            result_string += f"{original_string[previous_end:start]}{replacement_value}"
            previous_end = end
        result_string += original_string[previous_end:]
        return result_string


class MatchResultList(list):
    def all_values(self) -> Iterable:
        """
        Return all matched values over all results.
        """
        return itertools.chain(result.all_values() for result in self)

    def all_items(self) -> Iterable[tuple]:
        """
        Return all key/value combos of all results. Key for the unnamed groups is None.
        """
        return itertools.chain(result.all_items() for result in self)

    def replace(self, *with_values):
        """
        Replace matching groups with provided values, in order of matches, regardless of whether they are named or
        unnamed groups.

        Parameters are replacement values, or a single list of replacement values.
        """
        if not self:
            raise ValueError("replace() can only be used on successful match")
        if len(with_values) == 1:
            if type(with_values[0]) in (tuple, list):
                with_values = with_values[0]
        if not with_values:
            raise ValueError("Provide one or many values, or a single list of replacement values")

        string = self[0]._matches[0].string  # All matches have the same matched string
        replacement_values = iter(with_values)

        for result in self:
            string = result._replace_as_long_as_values_last(string, replacement_values)

        return string


class MatchObject(SimpleNamespace):

    def __bool__(self):
        return bool(self._matches)


class Matcher:
    def __init__(self, pattern: str = "*", case_sensitive: bool = True, flexible_spaces=True):
        self.converters = {}
        self._regex = None
        self.pattern = pattern
        self.case_sensitive = case_sensitive
        self.flexible_spaces = flexible_spaces

    @property
    def pattern(self):
        return self._pattern

    @pattern.setter
    def pattern(self, value):
        self._pattern = value
        self._regex = None

    @property
    def regex(self):
        if self._regex is None:
            self._regex = self._create_regex()
        return self._regex

    def _compile(self, pattern):
        return re.compile(pattern, flags=0 if self.case_sensitive else re.IGNORECASE)

    def match(self, string: str) -> MatchResult:
        return self._create_result(self._compile(self.regex).fullmatch(string))

    def match_start(self, string: str) -> MatchResult:
        return self._create_result(self._compile(f"^{self.regex}").match(string))

    def match_end(self, string: str) -> MatchResult:
        return self._create_result(self._compile(f"{self.regex}$").search(string))

    def search(self, string: str) -> MatchResult:
        return self._create_result(self._compile(self.regex).search(string))

    def search_all(self, string: str) -> MatchResultList:
        compiled = self._compile(self.regex)
        return MatchResultList(self._create_result(match_obj) for match_obj in compiled.finditer(string))

    def _create_result(self, single_match):
        if not single_match:
            result = MatchResult()
            result.unnamed = []
            result._matches = []
            return result

        else:
            result_dict = {
                key: value
                for key, value in single_match.groupdict().items()
                if value is not None
            }
            result = MatchResult(result_dict)
            result.unnamed = self._grouplist(single_match)
            result._matches = [single_match]
            for key, converter in self.converters.items():
                if type(key) is int:
                    raw_value = result.unnamed[key]
                    result.unnamed[key] = raw_value and converter(raw_value)
                else:
                    result[key] = converter(result[key])

            return result

    def _create_regex(self):
        pattern = self.pattern
        self.converters.clear()  # empty converters
        self._unnamed_group_index = 0
        wildcards = {
            "*": r".*",
            "+": r".",
            "?": r".?",
            "|": r"|",  # Not converted but can be escaped
        }

        result = pattern.translate(SPECIAL_CHARS)  # escape special chars

        for wildcard, actual in wildcards.items():
            not_escaped_pattern = fr"(?<!\[)\{wildcard}"
            escaped_pattern = fr"\[\{wildcard}]"
            result = re.sub(not_escaped_pattern, actual, result)
            result = re.sub(escaped_pattern, fr"\{wildcard}", result)

        result = re.sub(r"(?<!\[)\[([^]]*)]", self._field_repl, result)  # handle groups

        result = re.sub(r"\[\[", r"\[", result)
        result = re.sub(r"]]", r"]", result)
        if self.flexible_spaces:
            result = re.sub(" ", " +", result)

        return result

    def _field_repl(self, match_obj):
        group_string = match_obj.group(0).replace("\ ", "")
        name_regex = r"(\w+)"
        width_regex = r"(\d+)"

        # unnamed field, just increase the index
        match = re.search(r"\[]", group_string)
        if match:
            self._unnamed_group_index += 1
            return r"(.*)"

        # unnamed field with only width specifier
        match = re.search(fr"\[:{width_regex}]", group_string)
        if match:
            width = match.group(1)
            self._unnamed_group_index += 1
            return fr"(.{{{width}}})"

        # unnamed field with only the type annotation
        match = re.search(fr"\[:{name_regex}]", group_string)
        if match:
            type_ = match.groups()[0]
            # register this field with the name of the type to convert it later
            type_spec = registered_types.get(type_)
            if type_spec:
                self.converters[self._unnamed_group_index] = type_spec.converter
                self._unnamed_group_index += 1
                return fr"({type_spec.regex})"
            else:
                raise ValueError(
                    f"Unknown type {type_} - known types are: {','.join(registered_types.keys()) or 'None found'}"
                )

        # named field without type annotation
        match = re.search(fr"\[{name_regex}]", group_string)
        if match:
            name = match.group(1)
            return fr"(?P<{name}>.*)"

        # named field with width specifier
        match = re.search(fr"\[{name_regex}:{width_regex}]", group_string)
        if match:
            name, width = match.groups()
            return fr"(?P<{name}>.{{{width}}})"

        # named field with type annotation
        match = re.search(fr"\[{name_regex}:{name_regex}]", group_string)
        if match:
            name, type_ = match.groups()
            # register this field to convert it later
            type_spec = registered_types.get(type_)
            if type_spec:
                self.converters[name] = type_spec.converter
                return fr"(?P<{name}>{type_spec.regex})"
            else:
                raise ValueError(
                    f"Unknown type {type_} - known types are: {','.join(registered_types.keys()) or 'None found'}"
                )

    @staticmethod
    def _grouplist(match) -> list:
        """ Return unnamed match groups as a list. """
        # https://stackoverflow.com/a/53385788/300783
        named = match.groupdict()

        ignored_groups = {
            index - 1
            for name, index in match.re.groupindex.items()
            if name is None or name in named}

        return [group for i, group in enumerate(match.groups()) if i not in ignored_groups]

    def __repr__(self):
        return f'<Matcher("{self.pattern}")>'


class MultiMatcher:
    def __init__(self, patterns, case_sensitive: bool = True, flexible_spaces=True, strict: bool = False):
        """
        patterns: One of more qre patterns, all of which are matched/searched and results collected into one result
        case_sensitive: Whether case is considered when matching, default True.
        strict: Whether all patterns must match for the overall result to be a match. Default is False, partials are ok.
        """
        self.matchers = [
            Matcher(pattern, case_sensitive=case_sensitive, flexible_spaces=flexible_spaces) for pattern in patterns
        ]
        self.strict = strict

    @staticmethod
    def _matcher(property_name):
        def collect_results(self, string):
            result = getattr(self.matchers[0], property_name)(string)
            if not bool(result) and self.strict:
                return result
            for matcher in self.matchers[1:]:
                if bool(sub_result := getattr(matcher, property_name)(string)):
                    result.update(sub_result)
                    result.unnamed.extend(sub_result.unnamed)
                    result._matches.extend(sub_result._matches)
                elif self.strict:
                    return sub_result
            return result
        return collect_results

    match = _matcher("match")
    match_start = _matcher("match_start")
    match_end = _matcher("match_end")
    search = _matcher("search")
    search_all = _matcher("search_all")


def match(pattern, string, case_sensitive=True):
    return Matcher(pattern, case_sensitive=case_sensitive).match(string)


def match_start(pattern, string, case_sensitive=True):
    return Matcher(pattern, case_sensitive=case_sensitive).match_start(string)


def match_end(pattern, string, case_sensitive=True):
    return Matcher(pattern, case_sensitive=case_sensitive).match_end(string)


def search(pattern, string, case_sensitive=True):
    return Matcher(pattern, case_sensitive=case_sensitive).search(string)


def search_all(pattern, string, case_sensitive=True):
    return Matcher(pattern, case_sensitive=case_sensitive).search_all(string)


def to_regex(pattern):
    return Matcher(pattern).regex


if __name__ == "__main__":
    import json
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("pattern", help="A matching pattern")
    parser.add_argument("string", help="The string to match")
    parser.add_argument(
        "--regex", action="store_true", help="Show the generated regular expression"
    )
    args = parser.parse_args()
    matcher = Matcher(args.pattern)
    result = matcher.match(args.string)
    if matcher:
        print(json.dumps(result))
        if result.unnamed:
            print("Unnamed groups:", result.unnamed)
    if args.regex:
        print("Regex:", matcher.regex)
