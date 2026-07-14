# Loom Walkthrough Script (~3 minutes)

Record your screen with the repo open. One take is fine — a small stumble
reads as human. Delete this file (or keep it — it shows process) and put the
Loom link at the top of this folder's run-report or in the README.

## Setup before recording

- Terminal open in `mvp/`, font large
- `README.md`, `mvp/claims.yaml`, and `results/run-report.md` open in tabs
- Run `python detector.py --cached` once so you know it works

---

**[0:00–0:25] The bet** — on README:

> "Most architecture decisions die the moment the ADR is merged. Teams write
> them down, and then nothing ever re-reads the code against them. I built a
> detector that does — and spent most of the effort making sure it almost
> never speaks up over nothing. It's built against seven real ADRs from
> Backstage, Spotify's open-source project."

**[0:25–0:50] The translation layer** — scroll `claims.yaml`, stop on ADR014:

> "First product decision: an ADR is prose, not a rule. So each decision gets
> translated into a checkable claim — here, 'backend code must use native
> fetch, no third-party HTTP clients' — plus what a violation concretely looks
> like in a diff. This translation is where the real product thinking lives."

**[0:50–1:20] A real violation, flagged** — run `python detector.py --cached`,
point at the V-01 row:

> "Fifteen test PRs. This one adds axios to a backend plugin — deliberate,
> multiple call sites, a new dependency. Flagged at 0.96 confidence with the
> exact lines cited. That's the easy part."

**[1:20–2:10] The hard part: staying quiet** — point at N-04, then G-01:

> "The hard part is these. N-04 is a *confirmed* violation — a default export
> in a test fixture. The system stays silent anyway: one-off, trivial, zero
> blast radius. That's the linter's job, and a judgment layer that does the
> linter's job gets muted in a week.
>
> G-01 adds a banned library — but the PR description says 'OVERRIDE ADR014'
> with a tracked issue. The engineer did exactly what the process asks, so the
> system is structurally forbidden from flagging. Four guardrails like this
> run before the model is even called — including one for superseded ADRs, so
> it never enforces zombie rules."

**[2:10–2:40] The numbers and the miss** — `results/run-report.md`:

> "Result: four flags, all four worth an engineer's attention — 100%
> precision, zero false alarms across eleven silences. And one documented
> miss: a subtle violation at 0.68 confidence, below my 0.80 bar. I kept the
> miss. A wrong flag costs trust with the whole team; a miss costs one late
> catch, and repeated drift re-presents itself with higher severity. That
> asymmetry is the whole design."

**[2:40–3:00] Close:**

> "The metric I'd track in production isn't flags raised — it's the percentage
> of flags engineers mark useful. A drift detector is only a product if the
> team still has it installed in month two. Thesis memo, calibration rubric,
> and pilot plan are in the repo."

---

## After recording

1. Paste the Loom link into `README.md` under the headline (e.g.
   `**[3-min walkthrough](https://loom.com/...)**`)
2. Commit and push.
