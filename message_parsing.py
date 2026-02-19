from bs4 import BeautifulSoup


def _decode_part(part):
    payload = part.get_payload(decode=True)
    if payload is None:
        fallback_payload = part.get_payload()
        return fallback_payload if isinstance(fallback_payload, str) else ""

    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def extract_text(msg):
    plain_parts = []
    html_parts = []

    if msg.is_multipart():
        for part in msg.walk():
            if part.is_multipart():
                continue
            if part.get_content_disposition() == "attachment":
                continue

            content_type = part.get_content_type()
            if content_type == "text/plain":
                plain_parts.append(_decode_part(part))
            elif content_type == "text/html":
                html_text = BeautifulSoup(_decode_part(part), "html.parser").get_text(" ", strip=True)
                html_parts.append(html_text)
    else:
        content_type = msg.get_content_type()
        if content_type == "text/html":
            return BeautifulSoup(_decode_part(msg), "html.parser").get_text(" ", strip=True)
        return _decode_part(msg)

    if plain_parts:
        return "\n".join(part for part in plain_parts if part).strip()
    return "\n".join(part for part in html_parts if part).strip()


def parse_response_text(response_text):
    parsed = {}
    for line in response_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip().lower()] = value.strip()

    summary = parsed.get("summary", "No summary generated")
    category = parsed.get("category", "irrelevant").lower()
    if category not in {"spam", "irrelevant", "lead"}:
        category = "irrelevant"

    try:
        score = int(parsed.get("score", "0"))
    except ValueError:
        score = 0

    if category != "lead":
        score = 0
    else:
        score = max(1, min(score, 10))

    return summary, category, score
