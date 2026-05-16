function helper(): string { return "ok"; }

export class Service {
  doWork(): string { return "done"; }
}

export function root() {
  helper();
  const s = new Service();
  s.doWork();             // intra-fn binding: s -> Service
  const t: Service = new Service();
  t.doWork();             // annotation also binds
}
