# Product Thesis: Architecture Decisions Die the Moment the ADR Is Merged

> **Status: structured draft.** The argument and evidence are in place; sections
> marked `[YOUR VOICE]` need your own experience and phrasing before this ships
> to the portfolio — this memo is the piece interviewers will probe hardest.

## The bet

Teams don't lack architecture decisions — they lack any mechanism that notices
when the codebase quietly stops following them. The gap between "we decided X"
and "the code does X" is invisible until it surfaces as an incident, a
dependency audit, or a new hire asking "wait, which pattern is the real one?"

The bet: a **judgment-calibrated drift layer** — one that reads PRs the way a
staff engineer skims them, flags almost nothing, and is right when it does — is
a different product than either of the two things teams currently do, and it's
viable precisely because it optimizes for silence.

## Why the existing mechanisms fail (each one, specifically)

**ADR documents.** Write-only. Backstage's own ADR013→ADR014 supersession shows
decisions have lifecycles, but nothing re-reads old decisions against new code.
An ADR's enforcement power decays to zero within weeks of merge.

**Code review.** Reviewers check *this diff's* correctness, not conformance to
a decision made 14 months ago by people who may have left. V-03 in my test set
(msw quietly replaced across three test files, framed as "less boilerplate") is
exactly the PR that sails through review — it's tidy, it works, and the
reviewer never saw the ADR.

**Lint rules.** Great for the mechanical 20% (default exports), useless for the
judgmental 80% (is this re-export making the public API untraceable? is this
new dependency the exact sprawl we consolidated away?). And when a lint rule is
inconvenient mid-deadline, it gets `// eslint-disable`d — the drift now carries
an explicit marker of contempt for the rule.

`[YOUR VOICE]` — add one concrete story from your own experience of drift
discovered too late (an incident, an audit surprise, a "we have three HTTP
clients?" moment). This paragraph is what makes the memo yours.

## The counter-case, in full (steelman before rebuttal)

An engineering team's honest objections:

1. **"Another linter."** The org already ignores three bots on every PR. Adding
   a fourth that quotes year-old documents at people is noise with a halo of
   authority. *Answer:* this tool's core design goal is the opposite of the
   linter failure mode — it flagged 4 of 15 PRs on the test set, stayed silent
   on 11, and every silence has a logged reason. If its precision drops, the
   correct behavior is to raise its threshold, not defend its flags.

2. **"Second-guessed by an AI."** Engineers deviate deliberately all the time,
   for good reasons. *Answer:* deliberate deviation with a stated reason is
   guardrail-protected — a documented override in the PR description makes the
   system structurally silent. The tool only speaks when drift is unexplained.

3. **"The ADR is wrong, not the code."** Sometimes drift is the codebase
   voting. *Answer:* partially conceded — repeated drift against one ADR is a
   signal the *decision* needs revisiting, and the right v2 feature is exactly
   that report ("ADR010 has been overridden 4 times this quarter") aimed at the
   architecture owner, not PR authors.

`[YOUR VOICE]` — which of these objections do you find most convincing, and
would you actually concede more? Interviewers respect a position held with
visible cost.

## Why calibrated judgment is a different bet

Linting says: *every deviation is a violation.* Silence says: *no deviation is
knowable.* This tool says: *deviations are knowable, most don't matter, and
the product problem is deciding which few do.* That third position is only
defensible if the tool proves restraint — which is why precision (not recall,
not flag count) is the headline metric, why the miss on V-05 is documented
rather than tuned away, and why the guardrail spec is as long as the detection
logic.

## What kills this product

Named before launch: (1) precision below ~70% for even two weeks — trust never
recovers, uninstall follows; (2) ADR corpora too vague to extract checkable
claims from (the extraction step failed on ~2 of 8 real Backstage ADRs — some
decisions are genuinely not checkable and saying so matters); (3) the tool
being experienced as management surveillance rather than an engineering aid —
which is why flags go to the PR thread, visible to the author first, never to
a dashboard for their manager.
