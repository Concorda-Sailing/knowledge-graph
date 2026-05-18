"""Next.js client-side hooks plugin.

Activates when `next` is in npm deps. Contributes the canonical hooks
exported from `next/navigation`, `next/headers`, etc., so components
using them get classified as hooks. The plugin name is `nextjs-hooks`
to avoid colliding with the (future) `nextjs` depgraph plugin that
would handle file-routed endpoints — kept separate so each can evolve
independently.

Doc references:
  https://nextjs.org/docs/app/api-reference/functions

Note: file-routed endpoint detection (app/**/route.ts exporting
GET/POST/...; pages/api/**/*.ts default exports) is depgraph
extractor work, not cue contribution. Tracked separately.
"""
from kg.shared.plugins import Plugin, has_npm_dep

from depgraph.lib.classification.config import LanguageCues

PLUGIN = Plugin(
    name="nextjs-hooks",
    detect=lambda repo_path: has_npm_dep(repo_path, "next"),
    cues={
        "typescript": LanguageCues(
            hook_call_names={
                # next/navigation (app router)
                "useRouter", "usePathname", "useSearchParams",
                "useParams", "useSelectedLayoutSegment",
                "useSelectedLayoutSegments",
                # next/server-side helpers commonly used in client components
                # via re-exports — kept conservative; add when verified.
            },
        ),
    },
)
