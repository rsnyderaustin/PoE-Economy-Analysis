import re
from datetime import datetime, timezone
from typing import Iterable

from program_logging import LogsHandler, LogFile


def extract_average_from_text(text) -> float:
    values = extract_values_from_text(text)

    values = [sum(value) / len(value) if isinstance(value, Iterable) else value for value in values]
    avg_value = sum(values) / len(values)

    return avg_value


def extract_values_from_text(text) -> list:
    matches = re.findall(r'-?\d+(?:\.\d+)?(?:\s*[–-]\s*-?\d+(?:\.\d+)?)?', text)
    result = []
    for match in matches:
        clean = re.sub(r'[–—−-]', '-', match).strip()

        if '-' in clean[1:]:  # if there's a dash not at the start, it's a range
            left_str, right_str = clean.split('-', 1)
            left = float(left_str) if '.' in left_str else int(left_str)
            right = float(right_str) if '.' in right_str else int(right_str)
            result.append((left, right))
        else:
            val = float(clean) if '.' in clean else int(clean)
            result.append(val)
    return result


def _extract_from_brackets(match):
    parts = match.group(1).split('|')
    return parts[-1] if len(parts) > 1 else parts[0]


def sanitize_text(text: str):
    brackets_pattern = r'\[(.*?)\]'
    result = re.sub(brackets_pattern, _extract_from_brackets, text)
    result = result.strip().lower().replace(' ', '_')
    return result


def sanitize_dict_texts(d: dict):
    if isinstance(d, dict):
        return {k: sanitize_dict_texts(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [sanitize_dict_texts(item) for item in d]
    elif isinstance(d, str):
        return sanitize_text(d)
    else:
        return d


parse_log = LogsHandler().fetch_log(LogFile.API_PARSING)
def sanitize_mod_text(mod_text: str):
    # Replace any #-# with #_to_#
    mod_text = mod_text.strip().lower()
    result = re.sub(
        r'(-?\d+(?:\.\d+)?)\s*[–—−-]\s*(-?\d+(?:\.\d+)?)',
        r'\1_to_\2',
        mod_text
    )
    result = re.sub(r'\d+', 'n', result)
    result = result.replace('.n', '').replace('%', 'p')

    # Replace all non-alphabet characters with an underscore
    result = re.sub(r'[^a-zA-Z]', '_', result)
    # Filter multiple underscores into a singular underscore
    result = re.sub(r'_+', '_', result)

    brackets_pattern = r'\[(.*?)\]'
    result = re.sub(brackets_pattern, _extract_from_brackets, result)

    result = result.strip(' _')

    print(f"Sanitized {mod_text} -> {result}")
    parse_log.info(f"Sanitized {mod_text} -> {result}")

    return result


def format_date_into_utc(listing_date):
    if isinstance(listing_date, str):
        listing_date = listing_date.lower().replace("z", "+00:00")
        dt = datetime.fromisoformat(listing_date)
    elif isinstance(listing_date, datetime):
        dt = listing_date
    else:
        raise TypeError("Expected str or datetime.datetime")

    # Ensure it's timezone-aware in UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt

