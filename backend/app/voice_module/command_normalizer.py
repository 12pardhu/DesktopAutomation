from __future__ import annotations

import re


APP_NORMALIZATIONS = {
    "google chrome": "chrome",
    "chrome browser": "chrome",
    "microsoft edge": "edge",
    "mozilla firefox": "firefox",
    "visual studio code": "vs code",
    "vs code editor": "vs code",
    "file explorer": "explorer",
    "windows explorer": "explorer",
}


def normalize_spoken_command(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return cleaned

    lowered = cleaned.lower()
    for source, target in APP_NORMALIZATIONS.items():
        lowered = re.sub(rf"\b{re.escape(source)}\b", target, lowered)

    lowered = re.sub(r"\bplease\b", "", lowered)
    lowered = re.sub(r"\bkindly\b", "", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip(" .,")

    browser_type_match = re.search(
        r"open\s+(chrome|edge|firefox|safari|browser)\s+(?:and|then)\s+type(?:\s+in\s+the\s+(?:search|url)\s+bar)?(?:\s+as)?\s+(.+)",
        lowered,
    )
    if browser_type_match:
        app = browser_type_match.group(1).strip()
        content = _clean_search_phrase(browser_type_match.group(2))
        return f"open {app} and type in the url bar {content}".strip()

    browser_search_match = re.search(
        r"open\s+(chrome|edge|firefox|safari|browser)\s+(?:and|then)\s+(?:search\s+for|look\s+for)\s+(.+)",
        lowered,
    )
    if browser_search_match:
        app = browser_search_match.group(1).strip()
        content = _clean_search_phrase(browser_search_match.group(2))
        return f"open {app} and type in the url bar {content}".strip()

    lowered = re.sub(r"\bopen the\b", "open", lowered)
    lowered = re.sub(r"\bopen an\b", "open", lowered)
    lowered = re.sub(r"\bopen a\b", "open", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip(" .,")
    return lowered


def _clean_search_phrase(text: str) -> str:
    cleaned = text.strip(" .,\"'")
    cleaned = re.sub(r"^as\s+", "", cleaned)
    cleaned = re.sub(r"^for\s+", "", cleaned)
    if cleaned in {"youtube", "open youtube"}:
        return "youtube"
    return cleaned
