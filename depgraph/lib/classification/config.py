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
    """Cues that ship with the framework for JS/TS and Python.
    Per-project project.toml can extend this with custom cues."""
    return ClassificationConfig(languages={
        "python": LanguageCues(
            route_decorators={
                "router.get", "router.post", "router.put", "router.patch",
                "router.delete", "router.head", "router.options",
                "app.get", "app.post", "app.put", "app.patch", "app.delete",
            },
            orm_base_classes={
                "DeclarativeBase", "Base", "BaseModel",  # SQLAlchemy + project
            },
            test_framework_primitives={
                "pytest.fixture", "pytest.mark", "pytest.raises",
            },
            orm_schema_link_vias={"__tablename__"},
        ),
        "typescript": LanguageCues(
            # Express / Next.js API-route patterns are file-based for Next,
            # decorator-based for some Express-extension setups. Add as needed.
            route_decorators={
                "app.get", "app.post", "app.put", "app.patch", "app.delete",
                "router.get", "router.post", "router.put", "router.patch",
                "router.delete",
            },
            orm_base_classes={
                "Model", "BaseEntity",  # Prisma / TypeORM names
            },
            test_framework_primitives={"it", "test", "describe", "expect"},
            hook_call_names={
                "useState", "useEffect", "useMemo", "useCallback", "useRef",
                "useContext", "useReducer", "useLayoutEffect",
            },
            orm_schema_link_vias={"__tablename__"},
            # Future: add Prisma's "@@map" once a Prisma DSL extractor lands
        ),
    })
