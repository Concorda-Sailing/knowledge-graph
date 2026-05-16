// Fixture: re_export_chain — actual implementation (hop 1 of 3)
// This is the only file that declares primitives; barrels only re-export.

export class Widget {
  label: string;

  constructor(label: string) {
    this.label = label;
  }

  render(): string {
    return `<widget>${this.label}</widget>`;
  }
}

export function createWidget(label: string): Widget {
  return new Widget(label);
}
