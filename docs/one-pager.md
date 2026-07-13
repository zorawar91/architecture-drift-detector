# One-Pager: Drift Detection as a Code-Review-Assistant Feature

> **Status: structured draft.** Numbers and structure are real; `[YOUR VOICE]`
> markers need your positioning choices.

## Where it lives

A feature inside an existing code review assistant (the natural hosts: GitHub's
PR review bots, a Graphite/CodeRabbit-class reviewer, or an internal platform
team's PR tooling) — **not** a standalone product. Distribution and trust are
the whole game for a tool whose value is speaking rarely; it should ride inside
something engineers already accepted into their PRs.

`[YOUR VOICE]` — pick the one host you'd actually pitch and say why. (My
default: an internal platform team's PR bot, because the buyer — a platform
lead losing sleep over dependency sprawl — is also the ADR author, and pilot
access is a conversation, not a sales cycle.)

## The user and the moment

A staff/platform engineer who wrote (or inherited) the team's ADRs. The moment:
a PR is opened that quietly contradicts a documented decision, nobody in the
review thread knows the decision exists, and the deviation is about to become
the new de-facto standard. The feature posts one comment: the decision, the
specific lines, the confidence — and a "this was deliberate → link the issue"
escape hatch that trains the guardrail.

## The metric that isn't vanity

**Flag usefulness rate: % of flags the PR author or a reviewer marks as "worth
raising" (via 👍/👎 on the bot comment).** Target ≥ 70% in pilot.

Deliberately *not* the metric: flags raised, violations found, "drift caught."
All three reward noise — the exact failure mode that kills the category. A
secondary guard metric: **mute/uninstall rate** on the pilot team (any mute is
a pilot-ending event and gets a retro).

## Pilot plan

One team, 4 weeks, their own ADRs (5–8 extracted claims), shadow mode first:
two weeks of the bot writing flags to a log nobody sees, scored retroactively
with the pilot team's tech lead (calibrate on their judgment, not mine). Weeks
3–4: live comments, usefulness voting on. Exit criteria to expand: ≥70%
usefulness, zero mutes, and at least one flag the team says they'd have missed.

## Evidence from the MVP

100% precision (4/4 flags worth attention) and 11 correct silences on a
15-PR test set against real Backstage ADRs, including correct silence on a
documented override, a hotfix, an author's own follow-up, and a superseded
decision. One documented sub-threshold miss, kept as an accepted cost of
precision-first tuning. Full run: `results/run-report.md`.

## What I'd need to believe to invest further

`[YOUR VOICE]` — your honest bar. (Suggested: the shadow-mode usefulness rate
holding on a *second* team's ADR corpus, because generalizing across decision-
writing styles is this product's biggest unproven assumption.)
