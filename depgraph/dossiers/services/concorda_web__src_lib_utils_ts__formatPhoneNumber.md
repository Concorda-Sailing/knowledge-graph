---
node_id: concorda-web::src/lib/utils.ts::formatPhoneNumber
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e057ec3340bf5ba4b95f43bdff3747224ca0b2dbe7065fc8cf4a6db3a9b9ddf2
status: current
---

# formatPhoneNumber

## Purpose
Display-side formatter that turns a stored phone string (digits, possibly with stray punctuation, optional leading "1") into the canonical US presentation `(XXX) XXX-XXXX`. It is the read-side counterpart to `formatPhoneInput` (which formats as the user types) and exists so every surface that renders a phone — member directory, club detail page, club delegates admin, user dialog, profile form prefill — produces the same string without each callsite reinventing the regex. Storage is digits-only; this function is the single place that knows the presentation shape. If a future Claude is adding a new place that shows a phone, call this rather than hand-formatting.

## Invariants
- Input is treated as opaque: any non-digit characters are stripped before length checks. Do not assume callers pass clean digits.
- Exactly two shapes are recognized: 10 digits, or 11 digits with a leading `1` (NANP country code). Everything else returns the **original** input untouched — not an empty string, not "Invalid".
- Pure function: no I/O, no locale/timezone dependency, no React. Safe to call in render, in server components, and in form `defaultValues`.
- Output format is fixed to `(XXX) XXX-XXXX`. The space after `)` and the hyphen are load-bearing — `formatPhoneInput` produces the same shape so round-tripping through the profile form does not re-format.
- US-only by design. There is no E.164 / international branch.

## Gotchas
- The pass-through fallback is easy to miss: if a caller stores a 7-digit or malformed number, it renders raw. Directory/club pages currently trust the DB to hold 10-digit values; if that assumption breaks, garbage flows straight to the UI rather than throwing.
- `profile-form.tsx` and `user-dialog.tsx` feed the formatted output back into a controlled input whose `onChange` runs `formatPhoneInput`. The two formatters must keep producing the same canonical shape or the form will reformat on first keystroke and move the cursor.
- Two commits in history, both broad ("Add full web application…", "Add event management…"); no targeted fixes here yet. Treat the function as young rather than battle-hardened — edge cases (extensions, "+1 ", leading whitespace from CSV import) have not been reported but also have not been exercised.
- `replace(/\D/g, "")` strips a leading `+`, so `+16175551234` collapses to `16175551234` and hits the 11-digit branch correctly. Don't "improve" the regex without preserving this.

## Cross-cutting concerns
- Pure display layer — no auth, no audit, no side effects. PII surface, though: the formatted string lands in the member directory and club pages, which already gate on member-auth at the route level. This function does not enforce that gate.
- Used in both server components (directory page render) and client components (profile form, user dialog). Must stay free of browser-only APIs.

## External consumers
None known. No mobile/Expo callsite, no API response shaping, no email template — server-side rendering of phone numbers in emails/ICS would need its own helper or a shared port.

## Open questions
- Should the fallback branch log or surface malformed numbers instead of silently passing them through? Today there is no signal when a phone fails to format.
- Is US-only acceptable long-term? MBSA is regional, but the boat-finder/crew-finder roadmap could pull in non-US sailors; if so, this needs an E.164 path and storage normalization upstream.
