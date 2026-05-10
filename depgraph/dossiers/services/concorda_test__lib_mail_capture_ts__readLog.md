---
node_id: concorda-test::lib/mail-capture.ts::readLog
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cd91f1939be71dece8c6e97901b69597df43cdb1e75db617206320230bdd2d2f
status: current
---

# readLog

## Purpose

The `readLog` function is a low-level utility that retrieves and parses the captured email logs from a remote test environment. It executes an SSH command to run `docker exec` on a remote host, reading the raw log file and parsing each line as a JSON-serialized `CapturedEmail` object. This serves as the foundation for the `mailCapture` object, allowing tests to assert on email delivery and extract specific URLs (like invite or decision links) during end-to-end flows.

## Invariants

- **Returns an array of `CapturedEmail` objects.** If the command fails or the file is empty, it returns an empty array `[]` rather than throwing.
- **Relies on JSONL format.** Each line in the log file must be a valid, single-line JSON object representing a `CapturedEmail`.
- **Uses `execSync` for synchronous retrieval.** This assumes the caller is in a test environment where blocking the event loop for a brief I/O operation is acceptable.
- **Requires valid SSH credentials and host configuration.** The function depends on `SSH_KEY`, `SSH_USER`, `SSH_HOST`, and `CONTAINER` being correctly set in the environment.

## Gotchas

- **Requires remote SSH access.** Per commit `1e6d1b4`, this helper is specifically designed to work via `SSH+docker-exec` on a remote test host; it is not a local file-system reader.
- **Regex-based URL extraction is brittle.** The `extractInviteUrl` method uses a specific regex to distinguish between `PendingCrewInvite` paths (`/invite/{token}`) and member-based decision paths (`/members/invite/{accept|decline}/{id}`). If the URL structure for invites changes, this regex will fail to find the token.
- **`waitFor` can hang or time out.** If a test does not trigger an email, `waitFor` will poll every 250ms until the `deadline` is reached, eventually throwing an error that includes the `lastTail` of the log for debugging.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by all email-based E2E tests (e.g., `boat-crew` and `crew-request` flows) to verify that invitation links are correctly generated and delivered.

## External consumers

None known (internal to `concorda-test`).

## Open questions

- Should the `MailMatcher` subject support more complex pattern matching beyond `RegExp` or `string` to handle evolving email templates?
