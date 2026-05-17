import { Gadget, Tool } from './barrel';

export function build(): Gadget {
  const t = new Tool();
  t.use();
  return { size: 1 };
}
