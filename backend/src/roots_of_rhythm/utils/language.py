import re

_LANGUAGE_SUBTAG = re.compile(r"^[A-Za-z]{2,3}$")
_SCRIPT_SUBTAG = re.compile(r"^[A-Za-z]{4}$")
_REGION_SUBTAG = re.compile(r"^([A-Za-z]{2}|\d{3})$", re.ASCII)
_VARIANT_SUBTAG = re.compile(r"^(\d[A-Za-z0-9]{4,7}|[A-Za-z]{4})$", re.ASCII)
_ISRC = re.compile(r"^[A-Z]{2}[A-Z\d]{3}\d{7}$", re.ASCII)


def canonicalize_language_tag(value: str, *, error: type[Exception]) -> str:
    tag = value.strip()
    if not tag:
        raise error("language tag must not be empty")
    parts = tag.split("-")
    if not _LANGUAGE_SUBTAG.fullmatch(parts[0]):
        raise error("language tag must start with a valid language subtag")
    canonical = [parts[0].lower()]
    index = 1
    while index < len(parts):
        subtag = parts[index]
        if _SCRIPT_SUBTAG.fullmatch(subtag):
            canonical.append(subtag[0].upper() + subtag[1:].lower())
            index += 1
            continue
        if _REGION_SUBTAG.fullmatch(subtag):
            canonical.append(subtag.upper() if subtag.isalpha() else subtag)
            index += 1
            continue
        if _VARIANT_SUBTAG.fullmatch(subtag):
            canonical.append(subtag.lower())
            index += 1
            continue
        raise error("language tag contains an invalid subtag")
    return "-".join(canonical)


def normalize_isrc(value: str, *, error: type[Exception]) -> str:
    normalized = value.strip().replace("-", "").upper()
    if not _ISRC.fullmatch(normalized):
        raise error("ISRC must be a valid 12-character code")
    return normalized
