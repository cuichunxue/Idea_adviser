"""Idea Adviser: 発想法オーケストレーター.

入力内容を分析し、シックスハット法・TRIZ・逆転思考・ランダム発想法・
オズボーンのチェックリスト・SCAMPER・ソクラテス応答法の中から適切な
発想法を選び、その発想法のフレームワークに沿ってアイデアを論理的に
洗い出すためのライブラリ。
"""

from idea_adviser.orchestrator import Orchestrator, OrchestratorResult
from idea_adviser.methods import METHODS, Method, Step

__all__ = [
    "Orchestrator",
    "OrchestratorResult",
    "METHODS",
    "Method",
    "Step",
]
