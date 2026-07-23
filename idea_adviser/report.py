"""OrchestratorResult を人間が読みやすいレポート(Markdown)に整形する。"""

from __future__ import annotations

from idea_adviser.orchestrator import MethodRun, OrchestratorResult


def _format_method_run(run: MethodRun, index: int, switched_from_name: str | None = None) -> str:
    method = run.method
    score = run.score
    lines: list[str] = []

    header = f"## {index}. {method.name_ja} ({method.name_en})"
    lines.append(header)
    lines.append("")
    lines.append(f"> {method.summary}")
    lines.append("")

    if switched_from_name is not None:
        lines.append(
            f"**選定理由**: キーワードマッチでは{switched_from_name}が上位だったが、"
            "生成後の評価(適合度)がこちらの方が高かったため切り替えて採用。"
        )
    elif score.forced:
        lines.append(f"**選定理由**: {score.reason}")
    elif score.matched_keywords or score.matched_context:
        lines.append(f"**選定理由** (マッチ度スコア {score.score}): {score.reason}")
    else:
        lines.append(f"**選定理由**: {score.reason}")
    lines.append("")

    lines.append("**向いている場面**")
    for b in method.best_for:
        lines.append(f"- {b}")
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

    evaluation = run.evaluation
    if evaluation.evaluated:
        lines.append("")
        lines.append("### 評価・統合")
        lines.append(f"**適合度**: {evaluation.fit_score:.0f}/10"
                      "(この発想法が実際にこのお題に適していたか)")
        lines.append("")
        if evaluation.ranked_ideas:
            lines.append("**有望なアイデア(順位付け)**")
            for i, ranked in enumerate(evaluation.ranked_ideas, start=1):
                lines.append(f"{i}. **{ranked.idea}** (score: {ranked.score:.0f}/10) — {ranked.rationale}")
            lines.append("")
        if evaluation.recommendation:
            lines.append("**総合提案**")
            lines.append(f"> {evaluation.recommendation}")
            lines.append("")
        deep_dive = evaluation.deep_dive
        if deep_dive is not None:
            lines.append(f"**深掘り: {deep_dive.idea}**")
            if deep_dive.first_steps:
                lines.append("- 最初の一手:")
                for step_text in deep_dive.first_steps:
                    lines.append(f"  - {step_text}")
            if deep_dive.key_risks:
                lines.append("- 主要リスク・前提条件:")
                for risk in deep_dive.key_risks:
                    lines.append(f"  - {risk}")
            if deep_dive.success_metric:
                lines.append(f"- 成功指標: {deep_dive.success_metric}")

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

    if result.switched_from is not None:
        lines.append(
            f"(初回選定の**{result.switched_from.name_ja}**は評価の結果、適合度が低いと判断されたため、"
            f"**{result.runs[0].method.name_ja}**に切り替えました)"
        )
    lines.append("")

    for i, run in enumerate(result.runs, start=1):
        switched_from_name = (
            result.switched_from.name_ja if i == 1 and result.switched_from is not None else None
        )
        lines.append(_format_method_run(run, i, switched_from_name))
        lines.append("")

    other_scores = [s for s in result.all_scores if s.method.id not in {r.method.id for r in result.runs}]
    if other_scores:
        lines.append("---")
        lines.append("### 他に検討した発想法")
        for s in other_scores:
            lines.append(f"- {s.method.name_ja} (スコア {s.score})")

    return "\n".join(lines).rstrip() + "\n"
