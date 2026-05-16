// Fixture: generics_constraints
// Tests: class with 4 constrained type params, generic method on non-generic class,
// conditional type alias. attributes.template_parameters captures names only (no constraint text).

// Conditional type alias
export type Flatten<T> = T extends Array<infer U> ? U : T;

// Class with 4 type parameters, each with a constraint
export class Repository<
  TEntity extends object,
  TKey extends string | number,
  TFilter extends Record<string, unknown>,
  TResult extends TEntity | null
> {
  private items: Map<TKey, TEntity> = new Map();

  find(filter: TFilter): TResult {
    return null as unknown as TResult;
  }

  set(key: TKey, entity: TEntity): void {
    this.items.set(key, entity);
  }
}

// Non-generic class with a generic method
export class Transformer {
  transform<TIn, TOut extends TIn>(
    value: TIn,
    fn: (v: TIn) => TOut,
  ): TOut {
    return fn(value);
  }
}
