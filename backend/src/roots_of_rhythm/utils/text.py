from urllib.parse import urlsplit

_HTTP_SCHEMES = frozenset({"http", "https"})


def required_text(value: str, field: str, *, max_length: int, error: type[Exception]) -> str:
    normalized = value.strip()
    if not normalized:
        raise error(f"{field} must not be empty")
    if len(normalized) > max_length:
        raise error(f"{field} must be at most {max_length} characters")
    return normalized


def optional_text(value: str | None, field: str, *, max_length: int, error: type[Exception]) -> str | None:
    return None if value is None else required_text(value, field, max_length=max_length, error=error)


def optional_body_text(value: str | None, field: str, *, max_length: int, error: type[Exception]) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > max_length:
        raise error(f"{field} must be at most {max_length} characters")
    return normalized


def unique_texts(values: tuple[str, ...], field: str, *, max_length: int, error: type[Exception]) -> tuple[str, ...]:
    normalized = tuple(required_text(value, field, max_length=max_length, error=error) for value in values)
    folded = tuple(value.casefold() for value in normalized)
    if len(folded) != len(set(folded)):
        raise error(f"{field} must not contain duplicates")
    return normalized


def is_http_url(url: str) -> bool:
    parsed = urlsplit(url)
    return parsed.scheme in _HTTP_SCHEMES and bool(parsed.netloc)
