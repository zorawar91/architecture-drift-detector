#!/usr/bin/env python3
"""
Architecture Drift Detector — MVP

Scores PR diffs against structured ADR claims and, for each, either raises a
calibrated flag or deliberately stays silent.

Pipeline per PR:
  1. Pre-filter    — cheap regex match: which claims is this diff even about?
  2. Guardrails    — deterministic stay-silent rules, checked BEFORE any model
                     call (superseded ADR, documented override, hotfix/incident,
                     ADR author's own follow-up).
  3. LLM judgment  — does the diff violate the claim, with what confidence,
                     and how does it rate on the calibration rubric
                     (deliberate / repeated / blast radius)?
  4. Calibration   — flag only if: violation AND confidence >= 0.80 AND
                     rubric severity >= 2 of 3. Everything else stays silent,
                     with the reason logged.

Usage:
  python detector.py --cached           # replay cached model responses (no API key needed)
  python detector.py --live             # call the Anthropic API (needs ANTHROPIC_API_KEY)
  python detector.py --live --refresh-cache   # re-run live and overwrite the cache

Precision, not recall, is the design goal: a noisy version of this tool gets
uninstalled in a week.
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

HERE = Path(__file__).parent
CACHE_PATH = HERE / "cache" / "responses.json"
RESULTS_DIR = HERE.parent / "results"

CONFIDENCE_THRESHOLD = 0.80
SEVERITY_THRESHOLD = 2  # of 3 rubric factors (deliberate, repeated, blast radius)

MODEL = "claude-sonnet-4-5"

JUDGE_PROMPT = """You are reviewing a pull request diff against ONE documented \
architecture decision. Judge only this claim; ignore any other issues.

<decision id="{claim_id}">
Claim: {claim}
What a violation concretely looks like: {violation_looks_like}
Documented exceptions: {exceptions}
</decision>

<pull_request>
Title: {title}
Author: {author}
Description: {description}
</pull_request>

<diff>
{diff}
</diff>

Judge carefully:
- Only ADDED lines can violate. Deletions of a banned pattern are compliance, not drift.
- Content inside documentation/markdown code blocks quoting a pattern is not a violation.
- If a documented exception applies, it is NOT a violation.

Respond with ONLY a JSON object:
{{
  "violation": true/false,
  "confidence": 0.0-1.0,          // how certain you are of the verdict
  "evidence": "the specific added lines or dependency that violate, or why not",
  "deliberate": 0 or 1,           // does the PR look like an intentional pattern choice (vs. accidental)?
  "repeated": 0 or 1,             // multiple files/call sites, or a pattern others will copy?
  "blast_radius": 0 or 1          // public API / new dependency / infra divergence = 1; local & trivial = 0
}}"""


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_claims():
    data = yaml.safe_load((HERE / "claims.yaml").read_text())
    return data["claims"]


def load_prs():
    manifest = yaml.safe_load((HERE / "test_set" / "manifest.yaml").read_text())
    prs = manifest["prs"]
    for pr in prs:
        pr["diff"] = (HERE / "test_set" / pr["diff_file"]).read_text()
    return prs


# ---------------------------------------------------------------------------
# Stage 1: cheap pre-filter
# ---------------------------------------------------------------------------

def candidate_claims(pr, claims):
    """Which claims could this diff plausibly be about? Regex-cheap, generous."""
    hits = []
    for claim in claims:
        for pattern in claim.get("watch_patterns", []):
            if re.search(pattern, pr["diff"]):
                hits.append(claim)
                break
    return hits


# ---------------------------------------------------------------------------
# Stage 2: guardrails — deterministic stay-silent rules (run BEFORE the model)
# ---------------------------------------------------------------------------

# Calibration note (see results/run-report.md): v1 of this rule matched the bare
# word "incident" anywhere in a title, which silenced V-01 ("PagerDuty incident
# sync") — a false silence. Hotfix status must be structural (a label, a
# "hotfix:"/"revert:" title prefix, or an incident ticket reference), not topical.
HOTFIX_LABEL_RE = re.compile(r"\b(hotfix|incident|rollback|revert)\b", re.I)
HOTFIX_TITLE_RE = re.compile(r"^(hotfix|revert)\b|\bincident-\d+\b", re.I)
OVERRIDE_RE = re.compile(r"\b(override|exception|deviat\w+|waiv\w+)\b.*\bADR\s?-?\d+|"
                         r"\bADR\s?-?\d+\b.*\b(override|exception|deviat\w+|waiv\w+|follow-up)\b",
                         re.I | re.S)


def guardrail_check(pr, claim):
    """Return a stay-silent reason, or None if evaluation may proceed."""
    # Rule 0: never enforce a superseded/retired decision
    if claim.get("status") != "active":
        return (f"GUARDRAIL[superseded]: {claim['id']} is {claim.get('status')} "
                f"(by {claim.get('superseded_by', '?')}); zombie rules are never enforced")

    text = f"{pr['title']} {pr['description']}"
    claim_num = claim["id"].replace("ADR", "").lstrip("0")
    mentions_adr = re.search(rf"ADR\s?-?0*{claim_num}\b", text, re.I)

    # Rule 1: the ADR's own author making a deliberate, stated follow-up call
    if pr["author"] == claim.get("author") and mentions_adr:
        return (f"GUARDRAIL[author-override]: PR author wrote {claim['id']} and "
                "explicitly revisits it; that's governance working, not drift")

    # Rule 2: hotfix / incident response — never second-guess in the moment
    if any(HOTFIX_LABEL_RE.search(label) for label in pr.get("labels", [])) or \
            HOTFIX_TITLE_RE.search(pr["title"]):
        return "GUARDRAIL[hotfix]: incident/hotfix PR; follow-up belongs in the postmortem"

    # Rule 3: PR description explicitly references + overrides this ADR
    if mentions_adr and OVERRIDE_RE.search(text):
        return ("GUARDRAIL[documented-override]: PR explicitly references "
                f"{claim['id']} and declares a tracked exception")

    return None


# ---------------------------------------------------------------------------
# Stage 3: LLM judgment (live or cached)
# ---------------------------------------------------------------------------

def judge_live(pr, claim):
    import anthropic
    client = anthropic.Anthropic()
    prompt = JUDGE_PROMPT.format(
        claim_id=claim["id"],
        claim=claim["claim"].strip(),
        violation_looks_like="; ".join(claim.get("violation_looks_like", [])),
        exceptions="; ".join(claim.get("exceptions", [])) or "none",
        title=pr["title"],
        author=pr["author"],
        description=pr["description"].strip(),
        diff=pr["diff"],
    )
    msg = client.messages.create(
        model=MODEL, max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text
    match = re.search(r"\{.*\}", text, re.S)
    return json.loads(match.group(0))


def load_cache():
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def save_cache(cache):
    CACHE_PATH.parent.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


# ---------------------------------------------------------------------------
# Stage 4: calibration — turn a verdict into a flag or a deliberate silence
# ---------------------------------------------------------------------------

@dataclass
class Assessment:
    pr_id: str
    claim_id: str
    decision: str          # FLAG | SILENT
    reason: str
    confidence: float = None
    severity: int = None
    evidence: str = ""


def calibrate(pr, claim, verdict):
    conf = float(verdict["confidence"])
    if not verdict["violation"]:
        return Assessment(pr["id"], claim["id"], "SILENT",
                          "no violation found", conf, evidence=verdict["evidence"])
    severity = int(verdict.get("deliberate", 0)) + int(verdict.get("repeated", 0)) \
        + int(verdict.get("blast_radius", 0))
    if conf < CONFIDENCE_THRESHOLD:
        return Assessment(pr["id"], claim["id"], "SILENT",
                          f"below confidence threshold ({conf:.2f} < {CONFIDENCE_THRESHOLD})",
                          conf, severity, verdict["evidence"])
    if severity < SEVERITY_THRESHOLD:
        return Assessment(pr["id"], claim["id"], "SILENT",
                          f"violation confirmed but not worth an interrupt "
                          f"(rubric severity {severity}/3 < {SEVERITY_THRESHOLD}) — linter's lane",
                          conf, severity, verdict["evidence"])
    return Assessment(pr["id"], claim["id"], "FLAG",
                      f"calibrated flag (confidence {conf:.2f}, severity {severity}/3)",
                      conf, severity, verdict["evidence"])


# ---------------------------------------------------------------------------
# Runner + scoring
# ---------------------------------------------------------------------------

def run(mode, refresh_cache=False):
    claims = load_claims()
    prs = load_prs()
    cache = {} if refresh_cache else load_cache()
    assessments = []

    for pr in prs:
        pr_assessments = []
        for claim in candidate_claims(pr, claims):
            silent_reason = guardrail_check(pr, claim)
            if silent_reason:
                pr_assessments.append(
                    Assessment(pr["id"], claim["id"], "SILENT", silent_reason))
                continue

            key = f"{pr['id']}::{claim['id']}"
            if mode == "cached":
                if key not in cache:
                    sys.exit(f"Cache miss for {key}. Run with --live first.")
                verdict = cache[key]
            else:
                verdict = judge_live(pr, claim)
                cache[key] = verdict
            pr_assessments.append(calibrate(pr, claim, verdict))

        if not pr_assessments:
            pr_assessments.append(
                Assessment(pr["id"], "-", "SILENT", "no candidate claims matched (pre-filter)"))
        assessments.extend(pr_assessments)

    if mode == "live":
        save_cache(cache)
    return prs, assessments


def score(prs, assessments):
    """Compare detector decisions against ground truth; compute precision/recall."""
    truth = {pr["id"]: pr["ground_truth"]["decision"] for pr in prs}
    flagged_prs = {a.pr_id for a in assessments if a.decision == "FLAG"}
    should_flag = {pid for pid, d in truth.items() if d == "FLAG"}

    tp = flagged_prs & should_flag
    fp = flagged_prs - should_flag
    fn = should_flag - flagged_prs

    precision = len(tp) / len(flagged_prs) if flagged_prs else 1.0
    recall = len(tp) / len(should_flag) if should_flag else 1.0
    return dict(tp=sorted(tp), fp=sorted(fp), fn=sorted(fn),
                precision=precision, recall=recall,
                flags_raised=len(flagged_prs), worth_flagging=len(should_flag))


def report(prs, assessments, metrics, mode):
    lines = []
    w = lines.append
    w(f"# Detector run report ({mode} mode)\n")
    w(f"**Headline: {metrics['precision']:.0%} precision** — "
      f"{len(metrics['tp'])}/{metrics['flags_raised']} flags raised were worth an "
      f"engineer's attention. Recall {metrics['recall']:.0%} "
      f"({len(metrics['tp'])}/{metrics['worth_flagging']} of worth-flagging drift caught).\n")
    if metrics["fn"]:
        w(f"Documented misses (precision-first tradeoff): {', '.join(metrics['fn'])}\n")
    if metrics["fp"]:
        w(f"FALSE ALARMS (must fix): {', '.join(metrics['fp'])}\n")

    w("\n| PR | Claim | Decision | Ground truth | Match | Reason |")
    w("|----|-------|----------|--------------|-------|--------|")
    truth = {pr["id"]: pr["ground_truth"]["decision"] for pr in prs}
    pr_flagged = {a.pr_id for a in assessments if a.decision == "FLAG"}
    for a in assessments:
        gt = truth[a.pr_id]
        match = "✅" if (a.pr_id in pr_flagged) == (gt == "FLAG") else "❌"
        w(f"| {a.pr_id} | {a.claim_id} | **{a.decision}** | {gt} | {match} | {a.reason} |")

    w("\n## Evidence for flags\n")
    for a in assessments:
        if a.decision == "FLAG":
            w(f"- **{a.pr_id} / {a.claim_id}** (conf {a.confidence:.2f}, "
              f"severity {a.severity}/3): {a.evidence}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--cached", action="store_true", help="replay cached model responses")
    group.add_argument("--live", action="store_true", help="call the Anthropic API")
    ap.add_argument("--refresh-cache", action="store_true")
    args = ap.parse_args()

    mode = "cached" if args.cached else "live"
    if mode == "live" and not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY for --live mode (or use --cached).")

    prs, assessments = run(mode, args.refresh_cache)
    metrics = score(prs, assessments)
    text = report(prs, assessments, metrics, mode)
    print(text)

    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "run-report.md"
    out.write_text(text)
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
