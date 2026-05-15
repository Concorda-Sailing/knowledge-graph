"""Python sibling of canonical.ts. Only contains the slug helper used by the
parity gate test to compute the on-disk filename for a TS canonical node;
the rest of the canonicalization lives in canonical.ts and is invoked from
extract.ts via `npx tsx`.
"""
from __future__ import annotations

import re


def slugify_id_ts(node_id: str) -> str:
    """Slugify a canonical TS node id for on-disk filename.

    Mirrors extract_web.ts:72-74 (and canonical.ts:slugifyIdTs):
        id.replace(/::/g, "__").replace(/[^a-zA-Z0-9_]/g, "_").replace(/^_+|_+$/g, "")
    """
    s = node_id.replace("::", "__")
    s = re.sub(r"[^a-zA-Z0-9_]", "_", s)
    s = re.sub(r"^_+|_+$", "", s)
    return s
