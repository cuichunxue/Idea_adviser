"""入力内容から適切な発想法を選ぶロジック。

キーワードマッチによるスコアリングを基本としつつ、どの発想法とも
強くマッチしなかった場合は、網羅性が高く汎用的な発想法にフォール
バックする。選定結果には必ず「なぜその発想法を選んだか」という
理由(matched_keywords / reason)を添えて返す。これにより、選定過程
が論理的に追跡できるようにしている。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from idea_adviser.methods import METHODS, Method

# 特定のシグナルが見つからなかった場合の既定の発想法。
# 「網羅的な視点の確保」を謳うオズボーンのチェックリストは、
# お題を選ばず使える汎用的な発想法であるためフォールバックに適する。
DEFAULT_FALLBACK_METHOD_ID = "osborn_checklist"


@dataclass
class MethodScore:
    method: Method
    score: int
    matched_keywords: tuple[str, ...] = field(default_factory=tuple)
    reason: str = ""
    forced: bool = False


def _normalize(text: str) -> str:
    return text.strip().lower()


def score_methods(text: str) -> list[MethodScore]:
    """入力テキストに対する各発想法のマッチ度をスコアリングする。"""

    normalized = _normalize(text)
    results: list[MethodScore] = []
    for method in METHODS.values():
        matched = tuple(kw for kw in method.keywords if kw.lower() in normalized)
        score = len(matched)
        if matched:
            reason = (
                f"入力内容に「{'」「'.join(matched)}」に関連する語が見られたため、"
                f"{method.name_ja}が適していると判断しました。"
            )
        else:
            reason = ""
        results.append(MethodScore(method=method, score=score, matched_keywords=matched, reason=reason))

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
