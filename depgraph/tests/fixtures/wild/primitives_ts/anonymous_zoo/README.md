# anonymous_zoo

## What's tested

Default-exported anonymous functions, named function expressions assigned to variables,
and plain arrow functions. All three cases appear without a top-level `function Foo()` declaration.

## Why a naive extractor would break

A naive extractor that calls `fn.getName()` and filters on truthy results silently drops:

- `export default function() {}` — anonymous function expression export; `getName()` returns `undefined`
- `const handler = function myHandler() {}` — named function *expression* vs declaration; the name lives on the expression, not the declaration list
- `export default () => {}` — arrow function export; `getArrowFunctions()` or `getName()` returns nothing useful

The extractor must synthesize a name (`<default:module>`) for anonymous default exports and
pick up named function expressions via the variable declaration's name, not the expression's name.
