# Stay-Silent Guardrail Spec

Rules for when the system **must not flag** — checked deterministically, *before*
any model call. Guardrails are not confidence adjustments; they are hard gates.
If a guardrail applies, the model never gets a vote.

Ordering matters: cheaper, more absolute rules first.

## Rule 0 — Superseded decisions are never enforced

**Condition:** `claim.status != active`
**Rationale:** ADRs have lifecycles. Backstage's real ADR013 (use node-fetch) was superseded by ADR014 (use native fetch). A detector without lifecycle awareness would flag PRs for *complying with current policy* — enforcing zombie rules is the fastest possible way to lose trust.
**Test:** `G-04` migrates node-fetch → native fetch. Violates ADR013's text exactly. Correctly silent. ✅

## Rule 1 — The decision's author revisiting their own decision

**Condition:** PR author == ADR author AND the PR text explicitly references that ADR.
**Rationale:** The person who wrote the decision, deliberately and openly amending it, is governance working — not drift. Both conditions required: authorship alone is not a license to drift silently (an author violating their own ADR *without* mentioning it should still be evaluated).
**Test:** `G-03` — ADR010's author adds a scoped date-library exception with a stated follow-up. Correctly silent. ✅

## Rule 2 — Hotfix / incident response

**Condition:** hotfix/incident/rollback/revert label, `hotfix:`/`revert:` title prefix, or an incident ticket reference (`incident-NNNN`).
**Rationale:** Never second-guess an engineer mid-incident. The follow-up conversation belongs in the postmortem, where the team decides whether the shortcut becomes debt or gets reverted.
**Test:** `G-02` — incident-4521 hotfix stubs fetch directly (ADR007 shape). Correctly silent. ✅
**Calibration note:** v1 matched the bare word "incident" anywhere in a title and wrongly silenced `V-01` ("Add PagerDuty **incident** sync"). Fixed to require *structural* hotfix signals, not topical ones. Kept in the log deliberately — guardrails need calibration exactly like flags do; an over-broad guardrail is a false-negative machine.

## Rule 3 — Documented override in the PR

**Condition:** PR text references the specific ADR AND uses override language (override / exception / deviation / waiver, or ADR-follow-up phrasing).
**Rationale:** An engineer who names the rule and states why they're deviating — with a tracked issue — has done exactly what the ADR process asks. Flagging it says "we read your PR description and ignored it."
**Test:** `G-01` — "OVERRIDE ADR014: undici doesn't honor HTTPS_PROXY (issue #24988), scoped + removal tracked." Correctly silent. ✅

## Rules 4–5 — Applied after the model call (calibration layer)

- **Low confidence** (< 0.80): the system doesn't get to guess. Test: `V-05` (0.68) → silent, logged as an accepted miss.
- **Sub-threshold severity** (< 2/3): confirmed violations that are the linter's job, not an interrupt. Test: `N-04` → silent.

## The contrast case

A guardrail spec is only credible next to proof the system still speaks when it should: `V-01` (axios in a backend plugin, no override, no hotfix, no author claim) is flagged at 0.96 confidence in the same run where all four guardrail cases stay silent. The demo *is* that contrast — see `results/run-report.md`.

## Verification

All guardrail cases pass in `results/run-report.md`: 4/4 guardrail PRs silent, 0 flags suppressed incorrectly (after the Rule 2 fix), 1 real violation flagged alongside them.
