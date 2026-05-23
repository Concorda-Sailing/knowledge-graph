"""Negative case for #90: `obj["literal_key"](...)` is structurally
resolvable in principle (the key is a known string literal at parse
time), so we do NOT classify it as dynamic. Leave it on the legacy
`computed_callee` path.
"""


def call_literal(registry):
    return registry["doit"]()
