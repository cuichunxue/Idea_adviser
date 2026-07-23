"""入力内容から適切な発想法を選ぶロジック。

キーワードマッチによるスコアリングを基本としつつ、どの発想法とも
強くマッチしなかった場合は、網羅性が高く汎用的な発想法にフォール
バックする。選定結果には必ず「なぜその発想法を選んだか」という
理由(matched_keywords / reason)を添えて返す。これにより、選定過程
が論理的に追跡できるようにしている。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

from idea_adviser.methods import METHODS, Method

# 特定のシグナルが見つからなかった場合の既定の発想法。
# 「網羅的な視点の確保」を謳うオズボーンのチェックリストは、
# お題を選ばず使える汎用的な発想法であるためフォールバックに適する。
DEFAULT_FALLBACK_METHOD_ID = "osborn_checklist"

# 手がかり語(キーワード)の完全一致より重みを下げて扱う、
# best_for(向いている場面の説明文)から自動抽出した語。
KEYWORD_WEIGHT = 2
CONTEXT_WEIGHT = 1

# 漢字・カタカナが2文字以上連続する箇所を語として抽出する。
_TERM_PATTERN = re.compile(r"[一-鿿゠-ヿー]{2,}")

# best_for から抽出しても選定シグナルとして使わない、汎用的すぎる語。
# (どの発想法の説明文にも出てきうる/どんな入力にも出てきうる語)
_STOPWORDS = {
    "とき", "場合", "こと", "自分", "内容", "検討", "問題", "課題",
    "考え", "対応", "整理", "確認", "何か", "説明", "議論", "案件",
}


@dataclass
class MethodScore:
    method: Method
    score: int
    matched_keywords: tuple[str, ...] = field(default_factory=tuple)
    matched_context: tuple[str, ...] = field(default_factory=tuple)
    reason: str = ""
    forced: bool = False


def _normalize(text: str) -> str:
    return text.strip().lower()


def _extract_terms(text: str) -> set[str]:
    return {t for t in _TERM_PATTERN.findall(text) if t not in _STOPWORDS}


@lru_cache(maxsize=None)
def _context_terms(method_id: str) -> tuple[str, ...]:
    """best_for(向いている場面の説明・具体例)から選定用の語を自動抽出する。

    keywords に既に含まれる語は除き、best_for 由来の語だけを返す
    (完全一致キーワードより弱い重みで別集計するため)。
    """

    method = METHODS[method_id]
    keyword_set = {kw.lower() for kw in method.keywords}
    terms = _extract_terms(" ".join(method.best_for))
    return tuple(sorted(t for t in terms if t.lower() not in keyword_set))


def score_methods(text: str) -> list[MethodScore]:
    """入力テキストに対する各発想法のマッチ度をスコアリングする。

    完全一致するキーワード(method.keywords)を主シグナル(重み2)、
    best_for の説明文・具体例から自動抽出した語を副シグナル(重み1)
    として合算する。best_for は人間が読む「向いている場面」の定義で
    あると同時に、選定ロジック自身の入力にもなっている。
    """

    normalized = _normalize(text)
    results: list[MethodScore] = []
    for method in METHODS.values():
        matched_kw = tuple(kw for kw in method.keywords if kw.lower() in normalized)
        matched_ctx = tuple(t for t in _context_terms(method.id) if t.lower() in normalized)
        score = KEYWORD_WEIGHT * len(matched_kw) + CONTEXT_WEIGHT * len(matched_ctx)

        reason_parts = []
        if matched_kw:
            reason_parts.append(f"「{'」「'.join(matched_kw)}」に関連する語")
        if matched_ctx:
            reason_parts.append(f"向いている場面(「{'」「'.join(matched_ctx)}」)に関連する語")
        reason = (
            f"入力内容に{'、'.join(reason_parts)}が見られたため、{method.name_ja}が適していると判断しました。"
            if reason_parts
            else ""
        )

        results.append(
            MethodScore(
                method=method,
                score=score,
                matched_keywords=matched_kw,
                matched_context=matched_ctx,
                reason=reason,
            )
        )

    results.sort(key=lambda r: (-r.score, r.method.priority))
    return results


def select_methods(
    text: str,
    top_k: int = 1,
    method_id: str | None = None,
) -> list[MethodScore]:
    """発想法を選定する。

    Args:
        text: 入力内容(お題・課題文)。
        top_k: 何個の発想法を選ぶか。
        method_id: 指定した場合、選定ロジックを無視してこの発想法を強制選択する。
    """

    if method_id is not None:
        if method_id not in METHODS:
            raise KeyError(f"Unknown method id: {method_id!r}. Choose from {sorted(METHODS)}")
        method = METHODS[method_id]
        return [
            MethodScore(
                method=method,
                score=0,
                matched_keywords=(),
                reason=f"{method.name_ja}が明示的に指定されたため選択しました。",
                forced=True,
            )
        ]

    ranked = score_methods(text)
    top = ranked[:top_k]

    if all(r.score == 0 for r in top):
        fallback = METHODS[DEFAULT_FALLBACK_METHOD_ID]
        fallback_reason = (
            "入力内容から特定の発想法を強く示すシグナルが見つからなかったため、"
            f"どんなお題にも適用しやすい汎用的な発想法として{fallback.name_ja}を既定選択しました。"
        )
        result = [
            MethodScore(
                method=fallback,
                score=0,
                matched_keywords=(),
                reason=fallback_reason,
            )
        ]
        # top_k > 1 のときは、フォールバックに加えて次点のスコア0手法も
        # 参考として残しておく(理由なしとわかる形で)。
        result.extend(r for r in top if r.method.id != fallback.id)
        return result[:top_k] if top_k >= 1 else result

    return top
