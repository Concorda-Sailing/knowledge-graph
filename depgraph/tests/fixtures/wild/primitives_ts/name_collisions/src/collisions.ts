// Fixture: name_collisions
// The string "value" appears as: instance method, static method, class field, type alias.
// The :static suffix on the static method id is the key disambiguation.

// Type alias named "value" — lives at module scope
export type value = string | number;

export class Container {
  // Class field named "value"
  value: string = "";

  // Instance method named "value" — id collides with the field above (known limitation)
  getValue(): string {
    return this.value;
  }

  // Static method named "value:static" after extraction
  static value(input: unknown): string {
    return String(input);
  }
}
