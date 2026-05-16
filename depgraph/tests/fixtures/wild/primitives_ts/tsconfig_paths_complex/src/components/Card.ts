// Fixture: tsconfig_paths_complex — component accessed via @/components/Card alias
import { truncate } from "~lib/utils";

export class Card {
  constructor(public title: string) {}

  render(): string {
    return `<div>${truncate(this.title, 50)}</div>`;
  }
}
