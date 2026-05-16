// Fixture: jsx_corners
// Tests four JSX-adjacent patterns challenging naive returns_jsx detection.

import React from "react";

// Pattern 1: React.memo wrapper — the initializer is a CallExpression (memo(...)), not an
// ArrowFunction. The extractor emits this as a variable primitive, not a function primitive.
// returns_jsx is irrelevant for variables; the JSX inside memo's arg is invisible to the extractor.
export const MemoCard = React.memo(({ label }: { label: string }) => (
  <div>{label}</div>
));

// Pattern 2: function returning array of JSX elements — bodyHasJsx scans descendants,
// so the array wrapper does not hide the JSX nodes. returns_jsx=true.
export function CardList({ items }: { items: string[] }): JSX.Element[] {
  return items.map((item) => <li key={item}>{item}</li>);
}

// Pattern 3: conditional null return — one branch returns null, another returns JSX.
// bodyHasJsx finds JSX in the non-null branch → returns_jsx=true.
export function MaybeCard({ show }: { show: boolean }): JSX.Element | null {
  if (!show) return null;
  return <div className="card">content</div>;
}

// Pattern 4: JSX created but not returned — JSX lives in the body as a variable initializer,
// but the function returns void. bodyHasJsx still finds it → returns_jsx=true (pinned behavior).
export function sideEffectRender(container: HTMLElement): void {
  const el = <span>side effect</span>;
  container.innerHTML = el.toString();
}
