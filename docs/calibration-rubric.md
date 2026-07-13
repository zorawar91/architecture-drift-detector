# Calibration Rubric: What Is Worth Interrupting an Engineer For?

Written before tuning, anchored to real cases in `mvp/test_set/`. The detector's
job is not to find violations — it's to decide which violations deserve a human
interrupt. A "yes it violates" verdict is the *start* of the decision, not the end.

## The decision in one line

Flag only when: **verified violation** AND **confidence ≥ 0.80** AND **severity ≥ 2 of 3** on the factors below. Everything else is deliberate silence, with the reason logged.

## The three severity factors

| Factor | 1 point when | 0 points when | Why it matters |
|--------|--------------|---------------|----------------|
| **Deliberate** | The PR presents the deviating pattern as a choice ("used axios since it handles JSON out of the box") | The violation looks accidental or incidental | Deliberate deviations spread by imitation and signal the ADR has lost authority; accidents get fixed in review |
| **Repeated** | Multiple files/call sites, or the PR establishes a pattern others will copy (test conventions, client patterns) | A single isolated occurrence | One default export is a nit; three test files abandoning msw is a new de-facto convention |
| **Blast radius** | New dependency, public API surface, or shared infrastructure divergence | Local, trivial, mechanically fixable | The cost of drift compounds with the number of consumers who inherit it |

## Anchors from the test set (chosen before tuning)

**Worth flagging:**
- `V-01` — axios in a backend plugin: deliberate (stated), repeated (dep + 2 call sites), high blast (new HTTP client dependency). Severity 3/3. This is the archetype.
- `V-04` — root index re-exporting deep internals: deliberate, single PR, but it makes a *public API surface* untraceable. Severity 2/3. Shows severity ≥ 2 is the right bar — requiring 3/3 would miss this.

**Violation, but stay silent:**
- `N-04` — a default export in a test fixture. The verdict is confidently "violation" (0.90) and the correct decision is still silence: one-off, trivial, zero blast radius, and ADR003 itself says a lint rule is coming. **This case is the whole thesis** — a linter can't make this distinction; a judgment layer exists precisely to make it.

**Uncertain, so stay silent:**
- `V-05` — re-exports appearing in a non-index module. Real drift per ground truth, but the diff alone can't establish whether `columns.ts` is index-like (confidence 0.68). Below 0.80 → silent. **This is a known, accepted miss**: the cost of a wrong flag (trust erosion) exceeds the cost of this miss (caught later in review or repeat occurrence — and repetition raises severity next time).

## Why these thresholds

- **0.80 confidence**: below this, in manual review of the test set, the judge's evidence quality degraded from "cites specific added lines" to "reasonable inference." Flags must be defensible line-by-line to a skeptical engineer.
- **Severity ≥ 2**: severity-3-only missed V-04 (public API damage in a single, first-time change). Severity ≥ 1 would flag N-04 and turn the tool into a slower linter. 2 is where "worth an interrupt" lives on this test set.
- **Precision over recall, explicitly**: a false flag costs trust with the whole team and gets the bot muted; a miss costs one late catch, and repeated drift re-presents itself with higher severity. Asymmetric costs → asymmetric thresholds.

## What would change these numbers

Post-launch, thresholds recalibrate against the real metric (see one-pager): **% of flags engineers mark useful**. If that drops below ~70%, raise the confidence bar before touching anything else. If drift-caused incidents occur on PRs the tool silenced, revisit severity weighting — starting with blast radius.
