// Fixture: decorator_stack
// Tests: methods with 3+ stacked decorators including parameterized ones.
// signature.decorators must capture all names without argument lists.

function log(_target: any, _key: string, _desc: PropertyDescriptor) {}
function Role(_role: string) {
  return (_target: any, _key: string, _desc: PropertyDescriptor) => {};
}
function Guard(_perm: string, _level: number) {
  return (_target: any, _key: string, _desc: PropertyDescriptor) => {};
}
function Audit(_target: any, _key: string, _desc: PropertyDescriptor) {}
function Deprecated(_target: any, _key: string, _desc: PropertyDescriptor) {}

export class ApiController {
  // Three plain + one parameterized decorator
  @log
  @Role("admin")
  @Guard("write", 2)
  @Audit
  handleRequest(input: string): void {
    console.log(input);
  }

  // Five decorators, two parameterized
  @log
  @Role("superuser")
  @Guard("delete", 3)
  @Audit
  @Deprecated
  deleteRecord(id: number): boolean {
    return id > 0;
  }
}
