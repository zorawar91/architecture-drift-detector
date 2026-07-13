# Decision Memo: Why I Built the Quiet Version

**Audience:** VP Product · **Author:** Zoraawar Nandwal · **One page**

## The decision

I built an architecture-drift detector that is deliberately hard to trigger:
it flags a PR only when a violation of a documented architecture decision is
verified with ≥0.80 confidence AND scores ≥2/3 on a severity rubric
(deliberate, repeated, high blast radius) AND passes four hard stay-silent
guardrails. On the 15-PR test set it raised 4 flags — all 4 worth an
engineer's attention (100% precision) — and it knowingly missed one real
violation. I'm keeping the miss.

## Why quiet, when louder finds more

The alternatives were on the table. A recall-first version catches V-05 (the
subtle export-structure violation we missed) — but only by flagging at 0.68
confidence, and the same threshold change starts flagging cases like N-04, a
default export in a test fixture: a real violation that no engineer should be
interrupted for. Every dev-tool team knows how that movie ends — the bot gets
muted in week two, at which point its recall is zero anyway.

The asymmetry drove the call: a false flag costs trust with the entire team
and is nearly unrecoverable; a miss costs one late catch, and drift that
matters re-presents itself — with higher severity (it becomes "repeated"),
which raises its flag score next time. Misses self-correct; false alarms
compound.

## What I traded away and how it's controlled

- **80% recall, not 100%.** Controlled: the miss is logged with its
  confidence score, and repeat drift escalates by design.
- **Guardrails can hide real drift.** An engineer can game the override
  guardrail by name-dropping the ADR. Accepted for v1: an engineer who
  explicitly writes "overriding ADR014" in a PR description has created an
  auditable record — that's the ADR process working, even when it's used
  cheaply. v2 aggregates overrides per-ADR so gaming becomes visible at the
  decision level.
- **Guardrails themselves need calibration.** My first hotfix rule silenced a
  real violation because a PR *about* incident tooling contained the word
  "incident." Caught in testing, fixed to require structural signals, and
  kept in the run log — the failure mode of a guardrail is invisible (a false
  silence), so guardrails get test cases exactly like flags do.

## The evidence

15 PRs against 7 real Backstage ADRs: 4/4 flags correct, 11/11 correct
silences — including a documented override, an incident hotfix, an ADR
author's own amendment, and a superseded decision that a naive detector
would still enforce. `results/run-report.md` has every decision with its
logged reason.

## What I'd watch post-launch

One number: **% of flags engineers mark useful** (target ≥70%). Not flag
count — a rising flag count with falling usefulness is the tool failing while
looking productive. If usefulness holds on a second team's ADR corpus, invest;
if it doesn't, the extraction layer (prose → checkable claim) is the weak
joint, and that's where the next iteration goes.
