from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


validate_http_url = URLValidator(schemes=("http", "https"))


def public_image_url(request, image_field=None, external_url=""):
    """Return a safe absolute image URL, preserving valid external URLs."""
    candidates = [external_url]
    stored_name = None
    if image_field:
        try:
            stored_name = image_field.name
            if isinstance(stored_name, str) and stored_name.lower().startswith(("http://", "https://")):
                candidates.append(stored_name)
        except (ValueError, OSError):
            pass
        try:
            candidates.append(image_field.url)
        except (ValueError, OSError, AttributeError):
            pass
        if stored_name and not str(stored_name).lower().startswith(("http://", "https://")):
            candidates.append(stored_name)

    for candidate in candidates:
        if not isinstance(candidate, str):
            continue
        candidate = candidate.strip()
        if not candidate or any(character.isspace() for character in candidate):
            continue
        if candidate.lower().startswith(("http://", "https://")):
            try:
                validate_http_url(candidate)
                parsed = urlsplit(candidate)
                if parsed.hostname and not parsed.username and not parsed.password:
                    return candidate
            except (ValidationError, ValueError):
                continue
        elif "://" not in candidate:
            try:
                return request.build_absolute_uri(candidate)
            except (ValueError, TypeError):
                continue
    return None
