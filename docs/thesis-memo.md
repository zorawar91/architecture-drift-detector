# Product Thesis: Architecture Decisions Die the Moment the ADR Is Merged

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

I've watched this exact failure shape outside of code. At IQVIA, client
engagements start with a data specification everyone signs — which patient
universe, which projection methodology, how a "treated patient" is counted.
That spec is the ADR. Then monthly deliverables ship for two quarters, teams
rotate, and small interpretation choices accumulate quietly: a filter applied
slightly differently, a definition "improved" without anyone re-reading the
signed spec. Nobody notices — each deliverable looks internally consistent —
until the client's own QC tries to reconcile Q1 against Q3 and the numbers
don't tie out. What follows is weeks of re-baselining and, worse, a client now
double-checking everything we send. The spec didn't fail; the absence of
anything *re-reading deliverables against the spec* failed. That gap — between
a signed decision and its slow, invisible erosion — is the same product
problem this tool attacks, pointed at a codebase instead of a data deliverable.

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

Of the three, I concede the most ground to the third. Repeated drift against
one decision usually means the decision is losing the argument, not the
engineers — and a tool that keeps flagging PR authors in that situation is
enforcing a rule the team has already voted down with their keyboards. That's
why the roadmap's first real addition isn't better detection, it's the
per-ADR override report: when a decision gets deviated from four times in a
quarter, the flag should go to the decision's owner, phrased as "your ADR may
be stale," not to a fifth engineer.

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
