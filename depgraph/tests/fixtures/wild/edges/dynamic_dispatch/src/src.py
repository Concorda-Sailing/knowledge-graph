class Handler:
    def run(self):
        return "ok"

    def stop(self):
        return "stopped"


def dispatch(obj: Handler, name: str):
    # Dynamic dispatch: computed method name via getattr
    method = getattr(obj, name)
    result = method()
    return result


def dispatch_inline(obj: Handler, name: str):
    # Inline getattr call
    return getattr(obj, name)()
