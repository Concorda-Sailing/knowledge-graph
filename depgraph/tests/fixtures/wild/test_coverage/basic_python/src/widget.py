"""Production module covered by the fixture's test_widget.py."""


WIDGET_DEFAULT = "default"


def make_widget(name: str = WIDGET_DEFAULT) -> dict:
    return {"name": name, "kind": "widget"}
