"""OrchestratorResult を人間が読みやすいレポート(Markdown)に整形する。"""

from __future__ import annotations

from idea_adviser.orchestrator import MethodRun, OrchestratorResult


def _format_method_run(run: MethodRun, index: int) -> str:
    method = run.method
    score = run.score
    lines: list[str] = []

    header = f"## {index}. {method.name_ja} ({method.name_en})"
    lines.append(header)
    lines.append("")
    lines.append(f"> {method.summary}")
    lines.append("")

    if score.forced:
        lines.append(f"**選定理由**: {score.reason}")
    elif score.matched_keywords:
        lines.append(f"**選定理由** (マッチ度スコア {score.score}): {score.reason}")
    else:
        lines.append(f"**選定理由**: {score.reason}")
    lines.append("")

    lines.append("**この発想法の効果**")
    for b in method.benefits:
        lines.append(f"- {b}")
    lines.append("")

    lines.append("### アイデア出し")
    for step in run.steps:
        lines.append("")
        lines.append(f"#### {step.step_title}")
        lines.append(f"問い: {step.question}")
        lines.append("")
        for idea in step.ideas:
            lines.append(f"- {idea}")

    return "\n".join(lines)


def to_markdown(result: OrchestratorResult) -> str:
    lines: list[str] = []
    lines.append(f"# アイデア発想レポート: {result.topic}")
    lines.append("")

    if len(result.runs) == 1:
        lines.append(f"選定された発想法: **{result.runs[0].method.name_ja}**")
    else:
        names = " / ".join(r.method.name_ja for r in result.runs)
        lines.append(f"選定された発想法({len(result.runs)}件): **{names}**")
    lines.append("")

    for i, run in enumerate(result.runs, start=1):
        lines.append(_format_method_run(run, i))
        lines.append("")

    other_scores = [s for s in result.all_scores if s.method.id not in {r.method.id for r in result.runs}]
    if other_scores:
        lines.append("---")
        lines.append("### 他に検討した発想法")
        for s in other_scores:
            lines.append(f"- {s.method.name_ja} (スコア {s.score})")

    return "\n".join(lines).rstrip() + "\n"
