export class Base {}
export interface ISpeaker { speak(): void; }
export class Child extends Base implements ISpeaker { speak() {} }
