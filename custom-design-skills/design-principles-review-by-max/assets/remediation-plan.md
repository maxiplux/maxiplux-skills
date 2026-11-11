# Remediation plan: {{product or screen name}}

| | |
| --- | --- |
| Date | {{YYYY-MM-DD}} |
| Based on | {{evaluation report name or date}} |
| Findings covered | {{n}} of {{n}} open findings |
| Status | **Awaiting approval**: nothing has been changed yet |

## Summary

{{Two or three sentences: what will be fixed, in what order, and what is left for a decision.}}

## Fixes

{{One row per change set, highest severity first. A change set may close several findings.}}

| # | Change | Closes | Severity | Files | Risk | How it will be verified |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | {{what will change, concretely}} | {{F-ids}} | {{highest severity closed}} | {{paths}} | {{Low / Medium / High, with the reason}} | {{the original check, repeated}} |

## Needs your decision

{{Fixes that change product behavior, copy with legal or commercial meaning, or an API contract.
They are not applied without an explicit yes.}}

| Finding | Proposed change | Why it needs a decision |
| --- | --- | --- |
| {{F-id}} | {{…}} | {{…}} |

## Not in this plan

| Finding | Reason |
| --- | --- |
| {{F-id}} | {{third-party code / needs content from you / out of scope / severity 0}} |

## To approve

Reply with one of:

- **Approve all**: apply every fix in the table above, in order.
- **Approve some**: list the fix numbers to apply.
- **Change**: say what to do differently.

<!-- Filled in after the fixes are applied. -->
## Result

| # | Change | Status | Findings closed | Verification |
| --- | --- | --- | --- | --- |
| 1 | {{…}} | {{Applied / Partly applied / Not applied}} | {{F-ids}} | {{what was re-checked and the outcome}} |

Still open: {{F-ids and why, or "none"}}

---

— design-principles-review-by-max · by max
