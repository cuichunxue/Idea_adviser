"""発想法オーケストレーターの CLI。

使い方:
    python -m idea_adviser "検討したいお題やテーマ"
    python -m idea_adviser --file topic.txt --top-k 2
    python -m idea_adviser "..." --method scamper
    python -m idea_adviser "..." --use-llm   # ANTHROPIC_API_KEY が必要
"""

from __future__ import annotations

import argparse
import sys

from idea_adviser.generator import AnthropicGenerator, TemplateGenerator
from idea_adviser.methods import METHODS
from idea_adviser.orchestrator import Orchestrator
from idea_adviser.report import to_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="idea_adviser",
        description="入力内容に適した発想法を選び、アイデアを論理的に洗い出すオーケストレーター。",
    )
    parser.add_argument(
        "topic",
        nargs="?",
        help="検討したいお題・課題・テーマ。--file と併用不可。",
    )
    parser.add_argument("--file", "-f", help="お題をファイルから読み込む場合のパス。")
    parser.add_argument(
        "--method",
        "-m",
        choices=sorted(METHODS),
        default=None,
        help="発想法を自動選定せず、指定した発想法を強制的に使う。",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=1,
        help="自動選定する場合に、上位いくつの発想法を併用するか(既定: 1)。",
    )
    parser.add_argument(
        "--ideas-per-step",
        type=int,
        default=3,
        help="各ステップで生成するアイデア数(既定: 3。TemplateGenerator では意味を持たない)。",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Anthropic Claude API を使って実際にアイデアを生成する(ANTHROPIC_API_KEY が必要)。",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-5",
        help="--use-llm 使用時のモデル名(既定: claude-sonnet-5)。",
    )
    parser.add_argument("--output", "-o", help="レポートの出力先ファイル(省略時は標準出力)。")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.file and args.topic:
        parser.error("topic と --file は同時に指定できません。")

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            topic = f.read().strip()
    elif args.topic:
        topic = args.topic
    else:
        topic = sys.stdin.read().strip()

    if not topic:
        parser.error("お題が空です。引数、--file、または標準入力で指定してください。")

    generator = AnthropicGenerator(model=args.model) if args.use_llm else TemplateGenerator()
    orchestrator = Orchestrator(generator=generator, ideas_per_step=args.ideas_per_step)
    result = orchestrator.run(topic, top_k=args.top_k, method_id=args.method)
    report = to_markdown(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
    else:
        print(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
