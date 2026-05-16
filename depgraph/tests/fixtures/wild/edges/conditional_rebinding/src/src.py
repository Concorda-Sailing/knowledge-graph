class A:
    def do_work(self) -> str:
        return "A"


class B:
    def do_work(self) -> str:
        return "B"


def run(x: bool):
    if x:
        s = A()
    else:
        s = B()
    return s.do_work()
