"""Markdown → HTML rendering for dossier bodies. Strips frontmatter,
linkifies node ids and rule ids."""
from __future__ import annotations

import html
import re

try:
    import markdown as _md
    _MD_AVAILABLE = True
except ImportError:
    _MD_AVAILABLE = False


_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
_NODE_ID_RE = re.compile(
    r"`(concorda-(?:api|web|test|expo)::[^\s`]+::[^\s`]+|"
    r"(?:GET|POST|PUT|DELETE|PATCH)::/[^\s`]+|"
    r"rule::[a-zA-Z0-9_:]+|"
    r"resource::[a-zA-Z0-9_:]+|"
    r"role::[a-zA-Z0-9_:]+)`"
)


def strip_frontmatter(text: str) -> str:
    return _FRONTMATTER_RE.sub("", text, count=1)


def _link_ids(html_text: str) -> str:
    """After markdown renders, swap inline-code id strings for clickable links."""
    def repl(m: re.Match) -> str:
        nid = m.group(1)
        if nid.startswith("rule::"):
            href = f"/graph/rule/{nid}"
        elif nid.startswith(("resource::", "role::")):
            href = f"/graph/ontology/{nid}"
        else:
            href = f"/graph/node/{nid}"
        return f'<a class="idref" href="{href}"><code>{html.escape(nid)}</code></a>'
    # Match within already-rendered <code>X</code> spans
    code_re = re.compile(
        r"<code>(concorda-(?:api|web|test|expo)::[^<]+::[^<]+|"
        r"(?:GET|POST|PUT|DELETE|PATCH)::/[^<]+|"
        r"rule::[a-zA-Z0-9_:]+|"
        r"resource::[a-zA-Z0-9_:]+|"
        r"role::[a-zA-Z0-9_:]+)</code>"
    )
    return code_re.sub(repl, html_text)


def render(text: str) -> str:
    body = strip_frontmatter(text)
    if _MD_AVAILABLE:
        out = _md.markdown(
            body,
            extensions=["fenced_code", "tables", "sane_lists"],
        )
    else:
        # Plain-text fallback: escape and wrap in <pre>
        out = f"<pre>{html.escape(body)}</pre>"
    return _link_ids(out)


def first_paragraph(text: str, limit: int = 280) -> str:
    """First non-empty paragraph of body, plain text, truncated."""
    body = strip_frontmatter(text)
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    if not paras:
        return ""
    p = paras[0]
    # Strip leading ## headers
    p = re.sub(r"^#+\s*", "", p)
    if len(p) > limit:
        p = p[: limit - 1].rstrip() + "…"
    return p
