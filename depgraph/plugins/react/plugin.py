"""React framework plugin.

Activates when `react` is a project dependency (or peer dep). Contributes the
canonical React hook names — drives the `hook` classifier which keys on
identifier-call resolution against `external::npm::react::<hookName>`.

Component-detection (`returns_jsx`) is handled in the extractor and doesn't
need plugin cues today; if Vue/Svelte component detection lands later, each
would contribute its own component-classifier hook.
"""
from depgraph.lib.classification.config import LanguageCues
from kg.shared.plugins import Plugin, has_npm_dep

PLUGIN = Plugin(
    name="react",
    detect=lambda repo_path: has_npm_dep(repo_path, "react"),
    target_versions={"react": "19.2"},
    cues={
        "typescript": LanguageCues(
            hook_call_names={
                # React built-in hooks (16.8+ through current)
                "useState", "useEffect", "useMemo", "useCallback", "useRef",
                "useContext", "useReducer", "useLayoutEffect", "useImperativeHandle",
                "useDebugValue", "useDeferredValue", "useTransition", "useId",
                "useSyncExternalStore", "useInsertionEffect",
            },
        ),
    },
)
