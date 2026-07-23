"""選定精度の回帰テスト。

tests/test_selector.py の各テストは、手法名周辺の語をあえて含む
"作為的な" 文で選定ロジックの基本動作を確認している。
このファイルでは、ユーザーが実際に書きそうな自然な言い回しの課題文
(手法名やキーワードそのものを含まない)に対しても、正しい発想法が
選ばれることを確認する。best_for からの語句抽出(matched_context)が
機能していないと、これらのケースは軒並みフォールバック(スコア0)に
落ちて失敗する。
"""

import pytest

from idea_adviser.selector import select_methods

REALISTIC_CASES = [
    ("新しいカフェの出店計画について、上司に承認してもらうべきか迷っている", "six_hats"),
    ("工場のライン速度を上げたいが、上げると不良品率が増えてしまう", "triz"),
    ("毎回同じような企画しか思いつかず、チームの企画会議がマンネリ化している", "random"),
    ("自社のSaaSプロダクトのチャーン率を下げたい", "scamper"),
    ("この業界では対面営業が当たり前とされているが、本当にそれが最善か分からない", "reversal"),
    ("なぜ自分はこの転職をしたいのか、本当の動機が自分でも分かっていない", "socratic"),
    ("在庫管理システムの運用でヒューマンエラーが多発している。原因と対策を洗い出したい", "osborn_checklist"),
    ("子供向け知育玩具の新しいラインナップを考えたい", "scamper"),
    ("この新規事業に投資すべきかどうか、役員会に諮る前に整理したい", "six_hats"),
]


@pytest.mark.parametrize("text,expected_method_id", REALISTIC_CASES)
def test_realistic_phrasing_selects_expected_method(text, expected_method_id):
    result = select_methods(text)
    assert result[0].method.id == expected_method_id
    assert result[0].score > 0


DISTRACTOR_CASES = [
    "来月の家族旅行の計画を立てたい",
    "猫の名前を考えたい",
    "資格試験の勉強スケジュールを立てたい",
    "誕生日プレゼントを何にするか悩んでいる",
]


@pytest.mark.parametrize("text", DISTRACTOR_CASES)
def test_unrelated_topics_do_not_false_positive(text):
    """どの発想法とも関連しないお題では、スコア0のフォールバックになるべき。

    (=いずれかの発想法の語句抽出が緩すぎて誤ヒットしていないことの確認)
    """
    from idea_adviser.selector import score_methods

    ranked = score_methods(text)
    assert all(r.score == 0 for r in ranked)
