# Guardrail Test Log

Verification that the stay-silent rules hold — and one bug found and fixed.

## Run 1 (v1 hotfix rule) — FAILED

| Case | Expected | Got | Verdict |
|------|----------|-----|---------|
| V-01 axios in backend | FLAG | SILENT (hotfix guardrail) | ❌ false silence |

Cause: the hotfix rule matched the bare word "incident" anywhere in a title.
V-01's title — "Add PagerDuty **incident** sync" — is *about* incidents, not
an incident response. An over-broad guardrail is a false-negative machine, and
false silences are invisible in production; this only surfaced because the
guardrails have their own test cases.

Fix: hotfix status must be structural — a hotfix/incident label, a
`hotfix:`/`revert:` title prefix, or an incident ticket reference
(`incident-NNNN`) — never topical keywords.

## Run 2 (current) — PASSED

| Case | Rule exercised | Expected | Got |
|------|----------------|----------|-----|
| G-01 node-fetch w/ "OVERRIDE ADR014" + issue | documented-override | SILENT | SILENT ✅ |
| G-02 hotfix: incident-4521 fetch stub | hotfix | SILENT | SILENT ✅ |
| G-03 ADR010 author's own scoped exception | author-override | SILENT | SILENT ✅ |
| G-04 node-fetch → native fetch ("violates" superseded ADR013) | superseded | SILENT | SILENT ✅ |
| V-01 axios in backend, no excuse present | (none should fire) | FLAG | FLAG (0.96) ✅ |

The last row is the demo: a real violation flagged in the same run where all
four guardrail cases stay silent. Restraint only counts as a feature if the
system still speaks when it should.
