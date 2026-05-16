class Service:
    def do_work(self, x: int) -> str:
        return str(x)

    def cleanup(self) -> None:
        pass


def process(svc: Service, value: int) -> str:
    result = svc.do_work(value)
    svc.cleanup()
    return result
