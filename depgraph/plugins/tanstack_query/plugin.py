"""TanStack Query (formerly react-query) plugin.

Activates when `@tanstack/react-query` (v4+) or the legacy `react-query`
(v3) is in npm deps. Contributes the canonical data-fetching hooks so
components using `useQuery` / `useMutation` / `useInfiniteQuery` get
classified as hooks.

Doc references:
  https://tanstack.com/query/latest/docs/framework/react/reference/useQuery
  https://tanstack.com/query/latest/docs/framework/react/reference/useMutation
"""
from kg.shared.plugins import Plugin, has_npm_dep

from depgraph.lib.classification.config import LanguageCues

PLUGIN = Plugin(
    name="tanstack-query",
    detect=lambda repo_path: (
        has_npm_dep(repo_path, "@tanstack/react-query")
        or has_npm_dep(repo_path, "react-query")
    ),
    target_versions={"@tanstack/react-query": "5.62"},
    cues={
        "typescript": LanguageCues(
            hook_call_names={
                "useQuery", "useQueries", "useInfiniteQuery",
                "useMutation", "useIsFetching", "useIsMutating",
                "useQueryClient", "useSuspenseQuery",
                "useSuspenseInfiniteQuery", "useSuspenseQueries",
                "useQueryErrorResetBoundary",
            },
        ),
    },
)
