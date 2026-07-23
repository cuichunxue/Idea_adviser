"""発想法の各ステップに沿って、実際の「アイデア」を生成する部品。

``IdeaGenerator`` は、ステップの問いかけ(prompt)を受け取り、具体的な
アイデア文字列のリストを返すインターフェース。

- ``TemplateGenerator``: 外部APIなしで動く既定の実装。ステップの問いを
  お題に合わせて具体化した「検討すべき切り口」を返す。ネットワークや
  APIキーが無くても、発想法のロジックそのものは最後まで実行できる。
- ``AnthropicGenerator``: Claude (Anthropic API) を呼び出し、各ステップの
  問いに対する具体的なアイデアを生成する。APIキーが必要。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


class IdeaGenerator(Protocol):
    def generate(self, topic: str, step_title: str, step_question: str, n: int) -> list[str]:
        """1つのステップについて、topic に沿ったアイデアを n 件生成する。"""
        ...


@dataclass
class TemplateGenerator:
    """APIを使わず、発想法のステップを具体化した検討プロンプトを返す既定実装。

    創造的な内容そのものを合成することはせず、「何を考えるべきか」を
    お題に合わせて明確化することで、人間やLLMがすぐ書き足せる形にする。
    """

    def generate(self, topic: str, step_title: str, step_question: str, n: int) -> list[str]:
        return [
            "(未記入: ここに具体的なアイデアを書き出してください。"
            "AnthropicGenerator 等のLLM連携を使うと自動生成されます)",
        ]


@dataclass
class AnthropicGenerator:
    """Anthropic Claude API を使って各ステップのアイデアを生成する。"""

    model: str = "claude-sonnet-5"
    api_key: str | None = None
    max_tokens: int = 1024

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY が設定されていません。"
                "環境変数を設定するか、AnthropicGenerator(api_key=...) を指定してください。"
            )
        try:
            import anthropic  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ImportError(
                "AnthropicGenerator を使うには `pip install anthropic` が必要です。"
            ) from exc
        self._client = anthropic.Anthropic(api_key=self.api_key)

    def generate(self, topic: str, step_title: str, step_question: str, n: int) -> list[str]:
        prompt = (
            f"お題: {topic}\n"
            f"検討ステップ: {step_title}\n"
            f"問い: {step_question}\n\n"
            f"上記の問いに対する具体的で実行可能なアイデアを、日本語で{n}件、"
            "箇条書き(1行1アイデア、記号や番号を付けない)で出力してください。"
        )
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        ideas = [line.strip(" -・\t") for line in text.splitlines() if line.strip()]
        return ideas[:n] if ideas else []
