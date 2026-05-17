import { realFunc } from './barrel';

export { realFunc } from './barrel';

export function useFunc(): number {
  return realFunc();
}
