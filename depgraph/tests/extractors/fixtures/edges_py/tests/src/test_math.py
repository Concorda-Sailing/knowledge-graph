from .math import add, normalize
from .test_helpers import make_fixture

def test_add():
    x = make_fixture()           # helper call — NOT a subject
    assert add(1, 2) == 3        # subject: add
    assert normalize("X") == "x" # subject: normalize
