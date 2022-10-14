#!/usr/bin/env python3
"""
qre
"""
import itertools
import re
from typing import List

from qre.registered_types import register_type
from qre.registered_types import registered_types

__all__ = ["register_type", "Matcher", "match", "match_start", "match_end", "search", "search_all"]


# taken from the standard re module - minus "*+?[]", because that's our own syntax
SPECIAL_CHARS = {i: "\\" + chr(i) for i in b"(){}-^$\\.&~# \t\n\r\v\f"}


class MatchResult(dict):

    unnamed: list

    _is_match: bool

    def __bool__(self):
        return self._is_match

    def all_values(self):
        return itertools.chain(self.unnamed, self.values())

    def all_items(self):
        return itertools.chain(((None, value) for value in self.unnamed), self.items())


class Matcher:
    def __init__(self, pattern="*", case_sensitive=True):
        self.converters = {}
        self._regex = None
        self.pattern = pattern
        self.case_sensitive = case_sensitive

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

    def search_all(self, string: str) -> List[MatchResult]:
        compiled = self._compile(self.regex)
        return [self._create_result(match_obj) for match_obj in compiled.finditer(string)]

    def _create_result(self, single_match):
        if not single_match:
            result = MatchResult()
            result._is_match = False
            result.unnamed = []
            return result

        else:
            result_dict = {
                key: value
                for key, value in single_match.groupdict().items()
                if value is not None
            }
            result = MatchResult(result_dict)
            result._is_match = True
            result.unnamed = self._grouplist(single_match)
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
