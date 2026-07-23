"""発想法ごとに生成されたアイデアを評価し、最終的な提案に統合する部品。

``IdeaEvaluator`` は、選ばれた発想法とステップごとのアイデアを受け取り、

1. その発想法が本当にお題に適合していたか(``fit_score``)
2. 出てきたアイデアの中でどれが有望か(``ranked_ideas``)
3. 結局何をすべきか(``recommendation``)
4. 最有力の1案を、実行可能な最初の一手まで深掘りしたもの(``deep_dive``)

を返す。生の羅列を出すだけで終わらせず、評価・統合・深掘りまで行う
ことで、Tree-of-Thoughts のような「候補を比較し、有望なものを選ぶ」
工程を補う。全アイデアを深掘りすると呼び出し回数が膨らむため、
深掘りは最有力の1案だけに絞り、既存の評価呼び出し1回に含めることで
LLM呼び出し回数を増やさずに戦略的な深さを加える。

``TemplateGenerator``(API不要)で生成した空欄アイデアには意味のある
評価ができないため、既定は何もしない ``NullEvaluator``。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

from idea_adviser.generator import resolve_anthropic_client
from idea_adviser.methods import Method

if TYPE_CHECKING:
    from idea_adviser.orchestrator import StepResult


@dataclass
class RankedIdea:
    idea: str
    score: float
    rationale: str = ""


@dataclass
class DeepDive:
    """最有力の1案だけを対象にした、実行に踏み込んだ深掘り。"""

    idea: str
    first_steps: tuple[str, ...] = field(default_factory=tuple)
    key_risks: tuple[str, ...] = field(default_factory=tuple)
    success_metric: str = ""


@dataclass
class Evaluation:
    fit_score: float | None = None  # 0-10。None は「評価していない」ことを表す
    ranked_ideas: tuple[RankedIdea, ...] = field(default_factory=tuple)
    recommendation: str = ""
    deep_dive: DeepDive | None = None

    @property
    def evaluated(self) -> bool:
        return self.fit_score is not None


class IdeaEvaluator(Protocol):
    def evaluate(self, topic: str, method: Method, steps: list["StepResult"]) -> Evaluation:
        """生成済みのステップ結果を評価し、順位付けと統合提案を返す。"""
        ...


@dataclass
class NullEvaluator:
    """既定の評価器。何も評価せず、未評価の ``Evaluation`` を返す。

    API を使わない ``TemplateGenerator`` はプレースホルダーしか返さない
    ため、それを評価しても意味がない。評価しない場合は
    ``Orchestrator`` 側の手法切り替えロジックも作動しない
    (fit_score が None のままなので閾値判定に引っかからない)。
    """

    def evaluate(self, topic: str, method: Method, steps: list["StepResult"]) -> Evaluation:
        return Evaluation()


@dataclass
class AnthropicEvaluator:
    """Claude にアイデア群を評価・ランク付けさせ、最終提案に統合する。"""

    model: str = "claude-sonnet-5"
    api_key: str | None = None
    max_tokens: int = 1536
    top_n: int = 5

    def __post_init__(self) -> None:
        self._client = resolve_anthropic_client(self.api_key)

    def evaluate(self, topic: str, method: Method, steps: list["StepResult"]) -> Evaluation:
        ideas_block = "\n".join(
            f"[{step.step_title}] {idea}" for step in steps for idea in step.ideas
        )
        if not ideas_block.strip():
            return Evaluation()

        prompt = (
            f"お題: {topic}\n"
            f"適用した発想法: {method.name_ja}({method.summary})\n\n"
            "以下は、この発想法の各ステップに沿って出したアイデア案です。\n"
            f"{ideas_block}\n\n"
            "次の4点を、日本語で、JSONのみを出力して答えてください"
            "(説明文やコードフェンスは付けないでください):\n"
            "1. fit_score: この発想法がこのお題に対してどれだけ適切だったかを0〜10の整数で。\n"
            f"2. top_ideas: 上記アイデアの中から実行可能性・効果の観点で有望な順に最大{self.top_n}件選び、"
            "それぞれ idea(元の文言)・score(0〜10)・rationale(1文の理由)を含めること。\n"
            "3. recommendation: 結局何をすべきか、最も有望なアイデアを軸にした2〜4文の具体的な統合提案。\n"
            "4. deep_dive: top_ideas の中で最も有望な1案(idea)だけを対象に、"
            "実行に踏み込んで深掘りすること。first_steps(最初に着手すべき具体的な"
            "アクション2〜4件)、key_risks(実行を妨げうる主要リスクや前提条件2〜3件)、"
            "success_metric(成功したかどうかをどう測るか、1文)を含めること。\n\n"
            '出力形式: {"fit_score": <int>, "top_ideas": '
            '[{"idea": "...", "score": <number>, "rationale": "..."}], '
            '"recommendation": "...", "deep_dive": {"idea": "...", '
            '"first_steps": ["...", "..."], "key_risks": ["...", "..."], '
            '"success_metric": "..."}}'
        )
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        return _parse_evaluation(text)


_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _parse_evaluation(text: str) -> Evaluation:
    match = _JSON_FENCE.search(text)
    payload = match.group(1) if match else text
    try:
        data = json.loads(payload.strip())
        fit_score = data.get("fit_score")
        ranked = tuple(
            RankedIdea(
                idea=str(item.get("idea", "")),
                score=float(item.get("score", 0)),
                rationale=str(item.get("rationale", "")),
            )
            for item in data.get("top_ideas", [])
        )
        recommendation = str(data.get("recommendation", ""))

        deep_dive_data = data.get("deep_dive")
        deep_dive = None
        if isinstance(deep_dive_data, dict) and deep_dive_data.get("idea"):
            deep_dive = DeepDive(
                idea=str(deep_dive_data.get("idea", "")),
                first_steps=tuple(str(s) for s in deep_dive_data.get("first_steps", [])),
                key_risks=tuple(str(r) for r in deep_dive_data.get("key_risks", [])),
                success_metric=str(deep_dive_data.get("success_metric", "")),
            )

        return Evaluation(
            fit_score=float(fit_score) if fit_score is not None else None,
            ranked_ideas=ranked,
            recommendation=recommendation,
            deep_dive=deep_dive,
        )
    except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
        return Evaluation(recommendation="(評価結果の解析に失敗しました)")
