export const PI = 3.14;
export let counter = 0;
export const config: Record<string, string> = {};

export class Settings {
  static readonly VERSION = "1.0";
  private debug: boolean = false;
  publicProp: string;
}
