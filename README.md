# Architecture Drift Detector

**Most architecture decisions die the moment the ADR is merged. I built a
feature that watches for when code quietly stops following its own team's
rules — and spent most of the effort making sure it almost never speaks up
over nothing.**

Result on a 15-PR test set against real [Backstage](https://github.com/backstage/backstage)
ADRs: **100% precision** — 4 flags raised, all 4 worth an engineer's attention,
11 deliberate silences (every one with a logged reason), and one documented
miss I chose to keep.

## The problem

Teams document architecture decisions and then nothing re-reads them. Code
review checks the diff, not a decision made 14 months ago. Lint rules catch
the mechanical 20% and get `eslint-disable`d when inconvenient. So drift is
invisible until it's an incident, a dependency audit, or a new hire asking
which of the three HTTP clients is the real one.

The contrarian part: the scarce resource here isn't detection — an LLM can
read a diff against a rule. It's **restraint**. A drift detector that flags
everything is a slower linter, and linters that annoy people get muted. The
product problem is deciding when a violation is worth an engineer's attention
and proving the system stays quiet the rest of the time.

## What it does

For each PR, against 7 real Backstage ADRs translated into structured,
checkable claims ([`mvp/claims.yaml`](mvp/claims.yaml)):

1. **Pre-filter** — cheap regex: is this diff even about this decision?
2. **Guardrails** (before any model call) — hard silence on: superseded ADRs,
   documented overrides in the PR description, hotfix/incident PRs, and the
   ADR's own author revisiting their decision.
3. **LLM judgment** — violation verdict + confidence + severity rubric
   (deliberate / repeated / blast radius), with evidence cited from added lines.
4. **Calibration** — flag only at confidence ≥ 0.80 **and** severity ≥ 2/3.
   Everything else is silence with a logged reason.

## The run that matters

From [`results/run-report.md`](results/run-report.md):

| Case | What happens | Why it's the point |
|------|--------------|--------------------|
| `V-01` axios added to a backend plugin | **FLAG** (0.96, severity 3/3) | Real drift, caught with cited evidence |
| `N-01` `export default` for React.lazy | silent | Looks like a violation; is the ADR's documented exception |
| `N-04` default export in a test fixture | silent | **Confirmed violation, still silent** — one-off, trivial: the linter's job. This distinction is the thesis |
| `G-01` node-fetch with "OVERRIDE ADR014" + tracked issue | silent | Documented override → the system must not second-guess |
| `G-04` migrating node-fetch → native fetch | silent | "Violates" superseded ADR013; zombie rules are never enforced |
| `V-05` re-exports in a non-index module | silent (0.68) | **The documented miss.** Below the confidence bar — kept, because the cost of wrong flags exceeds the cost of this miss |

Precision 100% (4/4) · Recall 80% (4/5, one accepted miss) · False alarms 0/11.

## Repo map

- [`decision-memo.md`](decision-memo.md) — why I built the quiet version (the one-page VP read)
- [`docs/thesis-memo.md`](docs/thesis-memo.md) — the product bet and its steelmanned counter-case
- [`docs/calibration-rubric.md`](docs/calibration-rubric.md) — what "worth interrupting an engineer" means, anchored before tuning
- [`docs/guardrail-spec.md`](docs/guardrail-spec.md) — the four stay-silent rules, each with a passing test case (and one calibration bug kept in the log)
- [`docs/one-pager.md`](docs/one-pager.md) — where this lives as a product, and the one metric that isn't vanity
- [`mvp/`](mvp/) — detector, structured claims, 15-PR test set
- [`results/`](results/) — the full run report

## Run it

```bash
cd mvp
pip install pyyaml anthropic

python detector.py --cached   # replays cached judge responses; no API key needed
python detector.py --live     # re-judges everything (ANTHROPIC_API_KEY required)
```

## Honest notes

- The ADRs are real (Backstage's); the 15 PR diffs are **fabricated in
  Backstage's style** to exercise specific detector behaviors — the repo's
  real PR history doesn't ship labeled ground truth. Authors are fictional.
- Cached judge responses were generated with a Claude Sonnet-class model
  against the exact prompt in `detector.py`; `--live --refresh-cache`
  regenerates them.
- A 15-case set proves the *shape* of the calibration argument, not production
  readiness. The pilot plan in the one-pager is how the numbers would earn
  trust: shadow mode on a real team's ADRs, scored by their tech lead, not me.
