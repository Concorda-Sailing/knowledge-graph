# Plugin Authoring — Instructions for AI Agents

This document tells AI agents (Claude, Copilot, Cursor, etc.) how to
contribute a new framework plugin to this repo. Humans authoring plugins
should also read it — the same rules apply — but the strict tone here
is calibrated for autonomous agents that may not have full context on
the project's legal and reputational constraints.

---

## ⚠ HARD RULE: Open source only

**Only PR plugins for publicly distributed, open-source frameworks and
libraries.** This rule is not negotiable; it exists to protect both the
project maintainer and the agent's principal from liability.

### What "open source" means here

A framework qualifies for an upstream plugin PR if **all** of the
following hold:

1. The framework's source code is published under an
   [OSI-approved license](https://opensource.org/licenses) (MIT, Apache
   2.0, BSD, GPL, MPL, LGPL, ISC, etc.) **or** is unambiguously in the
   public domain.
2. The framework is distributed via a public registry (npm, PyPI,
   crates.io, RubyGems, Maven Central, etc.) **or** a public source
   forge (github.com, gitlab.com, codeberg.org, sourcehut, etc.) under
   that license.
3. The detection signal you use (the package name, the marker file
   pattern, the class name) is the framework's **publicly documented**
   surface — not something only an internal user would know.

If you cannot point to a public license file, a public package
manifest, and public documentation that mentions the cue strings
verbatim, the framework does not qualify. Stop and treat the work as
a private plugin (next section).

### What you MUST NOT publish

Do not submit a PR (and do not commit to this repository) for any
plugin that detects or contributes cues for:

- A private, internal, or proprietary codebase — anything not
  distributed publicly under an OSI-approved license.
- A commercial product whose source is closed, even if the SDK or
  client library happens to be on a public registry. (The detector for
  *the SDK as a library* might be fine; recognising patterns *internal
  to the closed product* is not.)
- An employer's internal framework, ORM, RPC system, test runner,
  config DSL, or any other in-house tooling, even if it shares a name
  with an open-source project. ("Acme's `pytest`-style internal test
  runner" is not the same as `pytest`.)
- A fork of an open-source project that the upstream maintainer has
  not made public.
- Anything where you are uncertain about the license, the distribution
  status, or the authorisation to publish.

**If you are unsure, you are not authorised. Stop.** Ask the
maintainer (or the agent's principal — the human directing this
work) for an explicit yes/no before submitting. "I think it's
probably open source" is not enough. Plugins, once merged and tagged,
can show up in third-party dossiers and security scans; reversing a
publication is much harder than holding it back.

### The right home for private detectors

Private/internal detectors *do* work — they just don't live in this
repository. The plugin loader supports project-local plugin paths
specifically so that organisations can ship their own detectors
without upstreaming. See the **"Local (project-private) plugins"**
section in [`README.md`](./README.md). The short version:

- Drop `<data-dir>/plugins/acme_internal_orm.py` in your project's
  knowledge-graph data dir.
- Or list custom paths under `[classification.plugins] local_paths`
  in `project.toml`.

Local plugins get the same first-class treatment as shipped ones —
detection, cue contribution, registry override on name collision —
without ever being published.

If an agent has been asked to "add a plugin for [proprietary thing]"
and is unsure whether the work should be a PR or a local file, the
default is **local**.

---

## What counts as a good upstream plugin

Beyond the open-source rule, a PR-worthy plugin:

- **Detects precisely.** False positives are worse than false
  negatives. A detector that fires on every TypeScript project because
  it grep'd for the word "router" is not acceptable.
- **Cues are canonical.** The patterns you contribute should be the
  framework's documented API surface — the names a tutorial would use,
  not project-specific aliases. Link to the relevant doc section in
  the plugin's docstring.
- **One framework per plugin.** Don't bundle "react + react-router +
  next.js" into one plugin. Each gets its own detector, its own cue
  set, and its own PR. Plugins compose; mega-plugins don't.
- **Small.** A plugin file is typically <50 LOC. If yours is bigger,
  reconsider whether multiple frameworks are being bundled.
- **No new dependencies.** Use the stdlib and the detection helpers in
  `base.py`. Adding `requests` or `tomli` to detect a framework is
  almost never the right answer.

---

## PR checklist

Before you submit a PR, confirm every one of these. Tick them off in
the PR description.

- [ ] **License verified.** Framework is OSI-licensed or public-domain.
      Link to the LICENSE file in the PR description.
- [ ] **Public distribution verified.** The framework is on npm /
      PyPI / a public source forge under that license. Link to it.
- [ ] **Cues are canonical.** Each cue string appears in the
      framework's official docs. Link the doc pages in the plugin's
      docstring or the PR description.
- [ ] **Plugin lives at `depgraph/plugins/<slug>/plugin.py`** with an
      empty `__init__.py` alongside.
- [ ] **`Plugin.name` matches the slug** (use kebab-case if the slug
      has multiple words: `name="react-router"`).
- [ ] **Detection helpers used where possible** (`has_npm_dep`,
      `has_pypi_dep`, `has_marker_file`). If you wrote a custom
      detector, explain why in the docstring.
- [ ] **Plugin docstring** explains: what the framework is, what
      activates the detector, what cues are contributed and why.
- [ ] **At least one registry test** under
      `depgraph/tests/test_plugin_registry.py` exercising detection
      AND cue contribution.
- [ ] **`pytest depgraph/tests` is green** locally before submission.
- [ ] **No false positive on a sibling framework's test repo.** If
      adding `vue`, confirm a React-only project does not activate
      `vue`. If adding `mocha`, confirm a `vitest`-only project does
      not activate `mocha`. Brief verification note in the PR.

---

## Authoring workflow

1. **Search for existing plugins.** `ls depgraph/plugins/` — make sure
   the framework isn't already shipped.

2. **Verify open-source status.** Find the LICENSE file. If you can't
   find one, stop. Do not proceed without explicit authorisation from
   the maintainer / principal.

3. **Read [`README.md`](./README.md) "Authoring a plugin"** for the
   worked NestJS example.

4. **Create the module:**

   ```bash
   mkdir depgraph/plugins/<slug>
   touch depgraph/plugins/<slug>/__init__.py
   ```

5. **Write `plugin.py`.** Keep it small. Cite the framework's doc URLs
   in the docstring.

6. **Add tests** to `depgraph/tests/test_plugin_registry.py`.

7. **Run the full suite:**

   ```bash
   .venv/bin/python -m pytest depgraph/tests -q
   ```

   All tests must pass. Do not skip the suite "because it's a small
   change" — the suite catches detection collisions you may not have
   anticipated.

8. **Commit.** Single commit per plugin. Message format:

   ```
   depgraph/plugins/<slug>: add detector + cues for <Framework>
   ```

   First-line body: one or two sentences explaining what the framework
   is and what cues you contribute. Cite the doc URLs you sourced
   cues from.

9. **PR title and body.**

   - Title: `depgraph/plugins: <framework> plugin`
   - Body:
     - One paragraph: what the framework is, link to its homepage.
     - License confirmation: `LICENSE: MIT` (or whatever) + link.
     - Distribution confirmation: link to the npm / PyPI page.
     - Cue justifications: each cue string with a link to the doc
       page where it appears.
     - Test note: which test asserts detection, which asserts cues.

---

## Naming conventions

- **Slug** matches the framework's most common public identifier (npm
  package name, PyPI distribution name, or the framework's own short
  name). Lowercase, kebab-case for multi-word.
- **`Plugin.name`** matches the slug exactly.
- **Python module/package name** is `slug.replace("-", "_")` (Python
  identifiers can't contain hyphens). If the resulting name would
  shadow a stdlib or popular third-party module (`pytest`, `requests`,
  `email`), suffix with `_plugin` — see how this repo's `pytest_plugin`
  avoids shadowing the actual `pytest` package on import.
- **Test names** start with `test_<slug>_detects_*` and
  `test_<slug>_contributes_*` for consistency.

---

## Code style

- Prefer lambdas for simple detectors:
  `detect=lambda repo_path: has_npm_dep(repo_path, "framework")`.
- Promote to a `_detect(repo_path) -> bool` named function only when
  the detector has more than one branch.
- Docstrings should answer three questions: what the framework is,
  what signal activates the detector, what cues are contributed and
  why those particular strings.
- No emojis in plugin source. (The repo-wide convention is no emojis
  in code; the user must explicitly request them.)

---

## When in doubt

- **License unclear?** Don't submit. Ask the maintainer.
- **Whether to bundle two frameworks?** Don't bundle. One plugin each.
- **Whether to upstream or keep local?** When unsure, keep local.
- **Whether your cue strings are the framework's canonical ones?**
  Link the doc page and let the reviewer judge.
- **Whether your detector is precise enough?** Test it against a
  sibling-framework repo and note the result in the PR body.

The cost of holding a PR back to verify is one round-trip. The cost
of publishing a plugin you weren't authorised to publish, or a
detector that fires on the wrong things, is much higher. Default to
caution.
