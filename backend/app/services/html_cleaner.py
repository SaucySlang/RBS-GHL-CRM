"""Context stripping for AI training input.

Takes a company homepage URL or raw pasted HTML/text and reduces it to
clean markdown-ish text: scripts, styles, tags and attributes are dropped;
headings, paragraphs, list items and links survive in readable form. Only
this cleaned text enters the LLM prompt context window.
"""
import re
from html import unescape
from html.parser import HTMLParser

import httpx

_BLOCKED_CONTAINERS = {"script", "style", "noscript", "template", "svg", "iframe", "head"}
_HEADINGS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}
_BLOCK_BREAKS = {"p", "div", "section", "article", "br", "tr", "table", "ul", "ol", "footer", "header", "main"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._parts: list[str] = []
        self._href: str | None = None
        self._link_text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in _BLOCKED_CONTAINERS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in _HEADINGS:
            self._parts.append(f"\n\n{_HEADINGS[tag]} ")
        elif tag == "li":
            self._parts.append("\n- ")
        elif tag == "a":
            self._href = dict(attrs).get("href")
            self._link_text = []
        elif tag in _BLOCK_BREAKS:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag in _BLOCKED_CONTAINERS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if tag == "a":
            text = "".join(self._link_text).strip()
            if text and self._href and self._href.startswith(("http", "/")):
                self._parts.append(f"[{text}]({self._href})")
            elif text:
                self._parts.append(text)
            self._href = None
            self._link_text = []
        elif tag in _HEADINGS:
            self._parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._href is not None:
            self._link_text.append(data)
        else:
            self._parts.append(data)

    def text(self) -> str:
        return "".join(self._parts)


def strip_html_to_markdown(raw: str) -> str:
    """Reduce raw HTML (or already-plain text) to clean markdown text."""
    if "<" not in raw:
        cleaned = raw
    else:
        parser = _TextExtractor()
        parser.feed(raw)
        parser.close()
        cleaned = parser.text()

    cleaned = unescape(cleaned)
    # Collapse runaway whitespace while keeping paragraph breaks
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r" ?\n ?", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


async def clean_training_input(source: str) -> str:
    """Accepts a URL or raw text/HTML; returns clean markdown context."""
    source = source.strip()
    if re.match(r"^https?://", source):
        async with httpx.AsyncClient(
            timeout=20, follow_redirects=True,
            headers={"User-Agent": "LeadStackBot/1.0 (+context-training)"},
        ) as client:
            resp = await client.get(source)
            resp.raise_for_status()
            return strip_html_to_markdown(resp.text)
    return strip_html_to_markdown(source)
