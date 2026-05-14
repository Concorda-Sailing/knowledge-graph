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
# The page chrome already renders the node title above the dossier body;
# a leading `# Title` in the markdown would duplicate it. Strip exactly
# one leading H1 if present. H2+ are untouched.
_LEADING_H1_RE = re.compile(r"\A\s*#\s+[^\n]+\n+")
# Repo basename pattern is permissive ([a-z][\w-]*) so the framework
# linkifies node ids from any project, not just one with a fixed repo
# naming scheme. False positives ("something::foo::bar" in a dossier
# that doesn't correspond to a real node) just render as a broken
# link — minor cost for project-agnostic linkification.
_NODE_ID_RE = re.compile(
    r"`((?:[a-z][\w-]*)::[^\s`]+::[^\s`]+|"
    r"(?:GET|POST|PUT|DELETE|PATCH)::/[^\s`]+|"
    r"rule::[a-zA-Z0-9_:]+|"
    r"resource::[a-zA-Z0-9_:]+|"
    r"role::[a-zA-Z0-9_:]+)`"
)


def strip_frontmatter(text: str) -> str:
    return _FRONTMATTER_RE.sub("", text, count=1)


def strip_leading_h1(text: str) -> str:
    return _LEADING_H1_RE.sub("", text, count=1)


def _link_ids(html_text: str) -> str:
    """After markdown renders, swap inline-code id strings for clickable links."""
    def repl(m: re.Match) -> str:
        nid = m.group(1)
        if nid.startswith("rule::"):
            href = f"/graph/rule/{nid}"
        elif nid.startswith(("resource::", "role::")):
            href = f"/graph/domain/{nid}"
        else:
            href = f"/graph/node/{nid}"
        return f'<a class="idref" href="{href}"><code>{html.escape(nid)}</code></a>'
    # Match within already-rendered <code>X</code> spans
    code_re = re.compile(
        r"<code>((?:[a-z][\w-]*)::[^<]+::[^<]+|"
        r"(?:GET|POST|PUT|DELETE|PATCH)::/[^<]+|"
        r"rule::[a-zA-Z0-9_:]+|"
        r"resource::[a-zA-Z0-9_:]+|"
        r"role::[a-zA-Z0-9_:]+)</code>"
    )
    return code_re.sub(repl, html_text)


_TABLE_RE = re.compile(r"<table>(.*?)</table>", re.DOTALL)


def _wrap_tables(html_text: str) -> str:
    """Wrap each rendered <table> in a scroll-x div so it can overflow
    cleanly on narrow viewports without forcing the whole dossier to
    scroll. Markdown's tables extension doesn't expose a wrapper option."""
    return _TABLE_RE.sub(
        lambda m: f'<div class="scroll-x"><table>{m.group(1)}</table></div>',
        html_text,
    )


def render(text: str) -> str:
    body = strip_leading_h1(strip_frontmatter(text))
    if _MD_AVAILABLE:
        out = _md.markdown(
            body,
            extensions=["fenced_code", "tables", "sane_lists"],
        )
    else:
        # Plain-text fallback: escape and wrap in <pre>
        out = f"<pre>{html.escape(body)}</pre>"
    return _link_ids(_wrap_tables(out))


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
