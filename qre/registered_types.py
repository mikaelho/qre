# `registered_types` is the dict of known types that is filled with register_type
import datetime
import decimal
import re
import uuid
from dataclasses import dataclass
from typing import Callable

registered_types = {}


@dataclass
class Conversion:
    regex: str
    converter: Callable


# a regex that ensures all groups to be non-capturing. Otherwise they would appear in
# the matches
TYPE_CLEANUP_REGEX = re.compile(r"(?<!\\)\((?!\?)")


def register_type(name, regex, converter=str):
    """ register a type to be available for the {value:type} matching syntax """
    cleaned = TYPE_CLEANUP_REGEX.sub("(?:", regex)
    registered_types[name] = Conversion(regex=cleaned, converter=converter)


# include some useful conversions
register_type("int", r"[+-]?[0-9]+", int)
register_type("float", r"[+-]?([0-9]*[.])?[0-9]+", float)
register_type("decimal", r"[+-]?([0-9]*[.])?[0-9]+", decimal.Decimal)
register_type("uuid", r"[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}", uuid.UUID)
register_type("date", r"\d{4}-\d{1,2}-\d{1,2}", datetime.date.fromisoformat)
register_type(
    "datetime",
    r"\d{4}-\d{1,2}-\d{1,2}"
    r"[T ]\d{1,2}:\d{1,2}"
    r"(?::\d{1,2}(?:[\.,]\d{1,6}\d{0,6})?)?"
    r"(Z|[+-]\d{2}(?::?\d{2})?)?",
    datetime.datetime.fromisoformat
)

# Basic patters
register_type("letters", r"[^\d_\W]+")
register_type("identifier", r"\w+")
register_type("open", r"((\[\[)|\(|\{)")
register_type("close", r"((\]\])|\)|\})")

# And some not so basic patterns
register_type("email", r"[\w.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
register_type(
    "url",
    (
        r"https?:\/\/(www\.)?[-\w@:%.\+~#=]{1,256}\.[\w()]{1,6}\b([-\w()!@:%\+.~#?&\/\/=]*)"
    ),
)

register_type(
    # Visa, MasterCard, American Express, Diners Club, Discover, JCB
    "creditcard",
    (
        r"(^4[0-9]{12}(?:[0-9]{3})?$)|(^(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6]["
        r"0-9]{2}|27[01][0-9]|2720)[0-9]{12}$)|(3[47][0-9]{13})|(^3(?:0[0-5]|[68][0-9])"
        r"[0-9]{11}$)|(^6(?:011|5[0-9]{2})[0-9]{12}$)|(^(?:2131|1800|35\d{3})\d{11}$)"
    ),
)
register_type(
    "ipv4",
    (
        r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}"
    ),
)
register_type(
    "ipv6",
    (
        r"(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA"
        r"-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){"
        r"1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3"
        r"}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0"
        r"-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:"
        r"(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5"
        r"]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0"
        r"-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,"
        r"3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"
    ),
)
