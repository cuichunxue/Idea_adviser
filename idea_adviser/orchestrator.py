"""発想法オーケストレーター。

入力内容(お題)を受け取り、
  1. どの発想法が適しているかを選定し(``selector``)、
  2. 選んだ発想法のフレームワーク(``methods``)に沿って、
  3. 各ステップごとにアイデアを生成し(``generator``)、
  4. 生成されたアイデアを評価・順位付けし、最終提案に統合する(``evaluator``)

という一連の流れを取りまとめ、論理的に構造化された結果を返す。

4番目の評価ステップは、単に発想法のテンプレートを埋めて終わりにせず、
「出てきた案のうちどれが有望か」「選んだ発想法は本当に適切だったか」を
判定する。評価の結果、選んだ発想法の適合度(fit_score)が低いと判断
された場合は、次点の発想法に自動で切り替える(1回まで)。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from idea_adviser.evaluator import Evaluation, IdeaEvaluator, NullEvaluator
from idea_adviser.generator import IdeaGenerator, TemplateGenerator
from idea_adviser.methods import Method
from idea_adviser.selector import MethodScore, select_methods

# 評価器が返す fit_score(0-10)がこの値未満の場合、次点の発想法へ
# 自動で切り替える(method_id 未指定・top_k=1 の自動選定モードのみ)。
FIT_SWITCH_THRESHOLD = 4.0


@dataclass
class StepResult:
    method_id: str
    step_title: str
    question: str
    ideas: list[str]


@dataclass
class MethodRun:
    method: Method
    score: MethodScore
    steps: list[StepResult]
    evaluation: Evaluation = field(default_factory=Evaluation)


@dataclass
class OrchestratorResult:
    topic: str
    runs: list[MethodRun]
    all_scores: list[MethodScore]
    switched_from: Method | None = None

    @property
    def primary(self) -> MethodRun:
        return self.runs[0]


class Orchestrator:
    """発想法の選定からアイデア出し・評価統合までを取りまとめるオーケストレーター。"""

    def __init__(
        self,
        generator: IdeaGenerator | None = None,
        evaluator: IdeaEvaluator | None = None,
        ideas_per_step: int = 3,
    ):
        self.generator = generator or TemplateGenerator()
        self.evaluator = evaluator or NullEvaluator()
        self.ideas_per_step = ideas_per_step

    def _build_run(self, topic: str, method_score: MethodScore) -> MethodRun:
        method = method_score.method
        steps: list[StepResult] = []
        for step in method.steps:
            question = step.render(topic)
            ideas = self.generator.generate(
                topic=topic,
                step_title=step.title,
                step_question=question,
                n=self.ideas_per_step,
            )
            steps.append(
                StepResult(
                    method_id=method.id,
                    step_title=step.title,
                    question=question,
                    ideas=ideas,
                )
            )
        return MethodRun(method=method, score=method_score, steps=steps)

    def run(
        self,
        topic: str,
        top_k: int = 1,
        method_id: str | None = None,
    ) -> OrchestratorResult:
        if not topic or not topic.strip():
            raise ValueError("topic (入力内容) を空にすることはできません。")

        # 自動選定・単一手法モード(method_id 未指定 かつ top_k=1)のときだけ、
        # 「適合度が低ければ次点に切り替える」バックトラックを行うため、
        # 次点の候補も1件多く取得しておく。
        auto_single = method_id is None and top_k == 1
        fetch_k = 2 if auto_single else max(top_k, 1)
        all_scores = select_methods(topic, top_k=fetch_k, method_id=method_id)

        primary_scores = all_scores[:1] if auto_single else all_scores[:top_k]
        runs = [self._build_run(topic, ms) for ms in primary_scores]
        for run in runs:
            run.evaluation = self.evaluator.evaluate(topic, run.method, run.steps)

        switched_from: Method | None = None
        if auto_single and len(all_scores) > 1:
            primary = runs[0]
            if (
                primary.evaluation.evaluated
                and primary.evaluation.fit_score < FIT_SWITCH_THRESHOLD
            ):
                fallback_run = self._build_run(topic, all_scores[1])
                fallback_run.evaluation = self.evaluator.evaluate(
                    topic, fallback_run.method, fallback_run.steps
                )
                fallback_is_better = (
                    not fallback_run.evaluation.evaluated
                    or fallback_run.evaluation.fit_score > primary.evaluation.fit_score
                )
                if fallback_is_better:
                    switched_from = primary.method
                    runs = [fallback_run]

        return OrchestratorResult(
            topic=topic, runs=runs, all_scores=all_scores, switched_from=switched_from
        )
