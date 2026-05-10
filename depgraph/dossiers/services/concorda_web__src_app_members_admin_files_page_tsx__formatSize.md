---
node_id: concorda-web::src/app/members/admin/files/page.tsx::formatSize
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c1e0964dc89f77e74efb7d3423c5c8ec6ad60d3a0f4930eda1d83ac0b4579ecc
status: current
---

# formatSize

## Purpose

A utility for converting raw byte counts into human-readable strings (B, KB, or MB). It is used within the `AdminFilesPage` to display file sizes in the media management table. It is distinct from `formatDate` (which handles time-based localization) and is intended for purely visual representation of file metadata.

## Invariants

- **Input is a number or undefined.** If the input is falsy (e.g., `0` or `undefined`), it returns the fallback string `"—"`.
- **Uses base-1024 scaling.** Calculations follow the standard binary prefix convention (1024 B = 1 KB).
- **Returns a string.** The output is always a string formatted with a single decimal place for KB and MB (e.g., `"1.2 MB"`).

## Gotchas

- **Zero-byte files return "—".** Because the function checks `if (!bytes)`, a file with exactly `0` bytes will return the fallback string `"—"` instead of `"0 B"`. If the UI requires showing an explicit `0 B` for empty files, this logic must be updated.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: None.
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.
