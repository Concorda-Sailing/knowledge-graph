"""Per-language cue maps for classification rules.

The classifier rule shapes are language-agnostic (e.g., "endpoint = function
decorated by a route registration"). The *cues* are per-language. This config
holds the cues so adding a new host language (Vue, Django, Yew, etc.) is a
matter of extending the maps, not editing classifier code.
"""
from dataclasses import dataclass, field


@dataclass
class LanguageCues:
    """Cues for one host language."""
    route_decorators: set[str] = field(default_factory=set)
    orm_base_classes: set[str] = field(default_factory=set)
    test_framework_primitives: set[str] = field(default_factory=set)
    hook_call_names: set[str] = field(default_factory=set)
    # Vias for cross-ref edges that mean "this class is the ORM mapper for
    # a schema." Used by the model classifier to distinguish mapper-style
    # references from incidental type references.
    orm_schema_link_vias: set[str] = field(default_factory=set)


@dataclass
class ClassificationConfig:
    """Aggregated cues across languages. Each classifier consumes the union
    or per-language subset as appropriate."""
    languages: dict[str, LanguageCues] = field(default_factory=dict)

    # Aggregated views, computed on access. Used by language-agnostic
    # classifiers (most of them).
    @property
    def route_decorators(self) -> set[str]:
        return {d for lang in self.languages.values() for d in lang.route_decorators}

    @property
    def orm_base_classes(self) -> set[str]:
        return {b for lang in self.languages.values() for b in lang.orm_base_classes}

    @property
    def test_framework_primitives(self) -> set[str]:
        return {p for lang in self.languages.values() for p in lang.test_framework_primitives}

    @property
    def hook_call_names(self) -> set[str]:
        return {h for lang in self.languages.values() for h in lang.hook_call_names}

    @property
    def orm_schema_link_vias(self) -> set[str]:
        return {v for lang in self.languages.values() for v in lang.orm_schema_link_vias}


def default_config() -> ClassificationConfig:
    """Cues from every shipped plugin, forced active.

    This is the convenience config for unit tests + CLI invocations that
    don't run through `depgraph.plugins.build_config_for_repos` (which does
    per-repo detection). Production regen calls the registry directly so
    only plugins whose detector fires contribute cues.

    The deferred import avoids a circular dependency:
    depgraph.plugins -> depgraph.lib.classification.config (this module).
    """
    from depgraph.plugins import _discover_plugins, _merge_cues

    languages: dict[str, LanguageCues] = {}
    for plugin in _discover_plugins():
        for lang, cues in plugin.cues.items():
            if lang in languages:
                languages[lang] = _merge_cues(languages[lang], cues)
            else:
                languages[lang] = LanguageCues(
                    route_decorators=set(cues.route_decorators),
                    orm_base_classes=set(cues.orm_base_classes),
                    test_framework_primitives=set(cues.test_framework_primitives),
                    hook_call_names=set(cues.hook_call_names),
                    orm_schema_link_vias=set(cues.orm_schema_link_vias),
                )
    return ClassificationConfig(languages=languages)
