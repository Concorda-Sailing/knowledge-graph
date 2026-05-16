def helper(): return "ok"

class Service:
    def do_work(self):
        return "done"

def root():
    helper()
    s = Service()
    s.do_work()             # intra-fn binding: s -> Service
    t: Service = Service()
    t.do_work()             # annotation also binds

def handler(svc: Service):
    svc.do_work()           # parameter annotation binds
