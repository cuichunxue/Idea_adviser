"""評価・統合ステップ(evaluator)と、それに基づく手法の自動切り替えのテスト。

実際のLLM呼び出しはせず、決定的な FakeEvaluator を使ってオーケストレーター側の
配線(評価結果を MethodRun に載せる/fit_score が低ければ次点に切り替える)を検証する。
"""

from dataclasses import dataclass

from idea_adviser.evaluator import Evaluation, NullEvaluator, RankedIdea
from idea_adviser.generator import TemplateGenerator
from idea_adviser.orchestrator import FIT_SWITCH_THRESHOLD, Orchestrator
from idea_adviser.report import to_markdown


@dataclass
class FakeGenerator:
    """常に非空のアイデアを返す(NullEvaluator と違い評価が意味を持つように)。"""

    def generate(self, topic, step_title, step_question, n):
        return [f"{step_title}のアイデア案"]


class FakeEvaluator:
    """method.id ごとに固定の fit_score を返す評価器。"""

    def __init__(self, scores: dict[str, float]):
        self.scores = scores
        self.calls: list[str] = []

    def evaluate(self, topic, method, steps):
        self.calls.append(method.id)
        return Evaluation(
            fit_score=self.scores.get(method.id, 5.0),
            ranked_ideas=(RankedIdea(idea="サンプル案", score=8.0, rationale="有望"),),
            recommendation=f"{method.name_ja}に基づく統合提案。",
        )


def test_null_evaluator_leaves_evaluation_unevaluated():
    orchestrator = Orchestrator(generator=TemplateGenerator(), evaluator=NullEvaluator())
    result = orchestrator.run("新商品の新機能アイデアを改良して考えたい")
    assert result.primary.evaluation.evaluated is False
    assert result.switched_from is None


def test_high_fit_score_does_not_trigger_switch():
    evaluator = FakeEvaluator(scores={"scamper": 9.0, "six_hats": 2.0})
    orchestrator = Orchestrator(generator=FakeGenerator(), evaluator=evaluator)
    result = orchestrator.run("新商品の新機能アイデアを改良して考えたい")

    assert result.primary.method.id == "scamper"
    assert result.primary.evaluation.fit_score == 9.0
    assert result.switched_from is None
    # 高スコアなので次点は評価すら呼ばれない
    assert evaluator.calls == ["scamper"]


def test_low_fit_score_triggers_switch_to_runner_up():
    # select_methods(top_k=2) の次点は six_hats(スコア0、priorityタイブレーク勝ち)。
    evaluator = FakeEvaluator(scores={"scamper": 1.0, "six_hats": 7.0})
    orchestrator = Orchestrator(generator=FakeGenerator(), evaluator=evaluator)
    result = orchestrator.run("新商品の新機能アイデアを改良して考えたい")

    assert result.switched_from is not None
    assert result.switched_from.id == "scamper"
    assert result.primary.method.id != "scamper"
    assert result.primary.evaluation.fit_score == 7.0
    assert evaluator.calls[0] == "scamper"
    assert len(evaluator.calls) == 2


def test_switch_does_not_happen_when_forced_method():
    evaluator = FakeEvaluator(scores={"scamper": 1.0})
    orchestrator = Orchestrator(generator=FakeGenerator(), evaluator=evaluator)
    result = orchestrator.run("何かのお題", method_id="scamper")

    assert result.primary.method.id == "scamper"
    assert result.switched_from is None


def test_switch_does_not_happen_when_top_k_greater_than_one():
    evaluator = FakeEvaluator(scores={"scamper": 1.0, "six_hats": 9.0})
    orchestrator = Orchestrator(generator=FakeGenerator(), evaluator=evaluator)
    result = orchestrator.run("新商品の新機能アイデアを改良して考えたい", top_k=2)

    assert result.switched_from is None
    assert len(result.runs) == 2


def test_fit_switch_threshold_is_reasonable():
    assert 0 < FIT_SWITCH_THRESHOLD < 10


def test_report_renders_evaluation_and_switch_note():
    evaluator = FakeEvaluator(scores={"scamper": 1.0, "six_hats": 7.0})
    orchestrator = Orchestrator(generator=FakeGenerator(), evaluator=evaluator)
    result = orchestrator.run("新商品の新機能アイデアを改良して考えたい")
    report = to_markdown(result)

    assert "評価・統合" in report
    assert "適合度" in report
    assert "総合提案" in report
    assert "サンプル案" in report
    assert "切り替えました" in report
    assert result.switched_from.name_ja in report
