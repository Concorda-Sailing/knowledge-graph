"""Test file deliberately excluded from the production graph — picked up
by the Option-C coverage walker."""
from src.widget import make_widget, WIDGET_DEFAULT


def test_make_widget_uses_default():
    w = make_widget()
    assert w["name"] == WIDGET_DEFAULT
    assert w["kind"] == "widget"


def test_make_widget_with_name():
    w = make_widget("custom")
    assert w["name"] == "custom"
