"""Next.js plugin — contributes UI-entry and API-client path conventions.

The web-api plugin handles HTTP-server flow shape; this one is purely
about Next.js's file-based conventions: pages/page.tsx routing, the
common locations API-client wrappers live, and where Next-style hooks
get organized. Activates on `next` in npm deps.
"""
from kg.shared.plugins import Plugin, has_npm_dep

from logigraph.plugins.base import LogigraphCues

PLUGIN = Plugin(
    name="nextjs",
    detect=lambda repo_path: has_npm_dep(repo_path, "next"),
    cues={"logigraph": LogigraphCues(
        ui_entry_path_globs={
            "app/**/page.tsx", "app/**/page.jsx",
            "pages/**/*.tsx", "pages/**/*.jsx",
            "src/app/**/page.tsx", "src/app/**/page.jsx",
            "src/pages/**/*.tsx", "src/pages/**/*.jsx",
        },
        api_client_path_globs={
            "lib/api.ts", "lib/api-client.ts", "lib/client.ts",
            "src/lib/api.ts", "src/lib/api-client.ts", "src/lib/client.ts",
        },
    )},
)
