"""発想法オーケストレーター。

入力内容(お題)を受け取り、
  1. どの発想法が適しているかを選定し(``selector``)、
  2. 選んだ発想法のフレームワーク(``methods``)に沿って、
  3. 各ステップごとにアイデアを生成する(``generator``)

という一連の流れを取りまとめ、論理的に構造化された結果を返す。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from idea_adviser.generator import IdeaGenerator, TemplateGenerator
from idea_adviser.methods import Method
from idea_adviser.selector import MethodScore, select_methods


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


@dataclass
class OrchestratorResult:
    topic: str
    runs: list[MethodRun]
    all_scores: list[MethodScore]

    @property
    def primary(self) -> MethodRun:
        return self.runs[0]


class Orchestrator:
    """発想法の選定からアイデア出しまでを取りまとめるオーケストレーター。"""

    def __init__(self, generator: IdeaGenerator | None = None, ideas_per_step: int = 3):
        self.generator = generator or TemplateGenerator()
        self.ideas_per_step = ideas_per_step

    def run(
        self,
        topic: str,
        top_k: int = 1,
        method_id: str | None = None,
    ) -> OrchestratorResult:
        if not topic or not topic.strip():
            raise ValueError("topic (入力内容) を空にすることはできません。")

        all_scores = select_methods(topic, top_k=max(top_k, 1), method_id=method_id)
        runs: list[MethodRun] = []

        for method_score in all_scores:
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
            runs.append(MethodRun(method=method, score=method_score, steps=steps))

        return OrchestratorResult(topic=topic, runs=runs, all_scores=all_scores)
