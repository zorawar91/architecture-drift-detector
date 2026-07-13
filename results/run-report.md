# Detector run report (cached mode)

**Headline: 100% precision** — 4/4 flags raised were worth an engineer's attention. Recall 80% (4/5 of worth-flagging drift caught).

Documented misses (precision-first tradeoff): V-05


| PR | Claim | Decision | Ground truth | Match | Reason |
|----|-------|----------|--------------|-------|--------|
| V-01 | ADR014 | **FLAG** | FLAG | ✅ | calibrated flag (confidence 0.96, severity 3/3) |
| V-01 | ADR013 | **SILENT** | FLAG | ✅ | GUARDRAIL[superseded]: ADR013 is superseded (by ADR014); zombie rules are never enforced |
| V-02 | ADR010 | **FLAG** | FLAG | ✅ | calibrated flag (confidence 0.95, severity 3/3) |
| V-03 | ADR007 | **FLAG** | FLAG | ✅ | calibrated flag (confidence 0.90, severity 3/3) |
| V-04 | ADR004 | **FLAG** | FLAG | ✅ | calibrated flag (confidence 0.86, severity 2/3) |
| V-05 | ADR004 | **SILENT** | FLAG | ❌ | below confidence threshold (0.68 < 0.8) |
| N-01 | ADR003 | **SILENT** | SILENT | ✅ | no violation found |
| N-02 | ADR014 | **SILENT** | SILENT | ✅ | no violation found |
| N-02 | ADR013 | **SILENT** | SILENT | ✅ | GUARDRAIL[superseded]: ADR013 is superseded (by ADR014); zombie rules are never enforced |
| N-03 | ADR006 | **SILENT** | SILENT | ✅ | no violation found |
| N-04 | ADR003 | **SILENT** | SILENT | ✅ | violation confirmed but not worth an interrupt (rubric severity 0/3 < 2) — linter's lane |
| G-01 | ADR014 | **SILENT** | SILENT | ✅ | GUARDRAIL[documented-override]: PR explicitly references ADR014 and declares a tracked exception |
| G-01 | ADR013 | **SILENT** | SILENT | ✅ | GUARDRAIL[superseded]: ADR013 is superseded (by ADR014); zombie rules are never enforced |
| G-02 | ADR007 | **SILENT** | SILENT | ✅ | GUARDRAIL[hotfix]: incident/hotfix PR; follow-up belongs in the postmortem |
| G-03 | ADR010 | **SILENT** | SILENT | ✅ | GUARDRAIL[author-override]: PR author wrote ADR010 and explicitly revisits it; that's governance working, not drift |
| G-04 | ADR014 | **SILENT** | SILENT | ✅ | no violation found |
| G-04 | ADR013 | **SILENT** | SILENT | ✅ | GUARDRAIL[superseded]: ADR013 is superseded (by ADR014); zombie rules are never enforced |
| C-01 | ADR004 | **SILENT** | SILENT | ✅ | no violation found |
| C-02 | ADR013 | **SILENT** | SILENT | ✅ | GUARDRAIL[superseded]: ADR013 is superseded (by ADR014); zombie rules are never enforced |

## Evidence for flags

- **V-01 / ADR014** (conf 0.96, severity 3/3): Adds axios ^1.7.2 to plugins/pagerduty-backend/package.json and replaces two native fetch call sites in PagerDutyClient.ts with axios.get; backend (Node.js) package, and the description states axios was chosen deliberately.
- **V-02 / ADR010** (conf 0.95, severity 3/3): Adds moment ^2.30.1 as a dependency and imports it in TaskDuration.tsx and TaskList.tsx for relative/localized formatting — the exact use case ADR010 assigns to Luxon; moment is the specific library the ADR sunset.
- **V-03 / ADR007** (conf 0.90, severity 3/3): Replaces msw handlers with global.fetch = jest.fn() / jest.spyOn(global, 'fetch') across three test files (CatalogClient, EntityClient, LocationClient); the description frames it as the new preferred pattern.
- **V-04 / ADR004** (conf 0.86, severity 2/3): Root src/index.ts adds re-exports from './components/Table/internals/VirtualizedRow' and a deeper hooks path, bypassing the components and Table index files — exported symbols are no longer traceable through index files.