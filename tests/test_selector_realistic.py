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
    # --- 追加バッテリー: 各手法2〜4件、実務でありそうなテーマ ---
    ("新しいオフィスに移転すべきかどうか、経営会議で決めなければならない", "six_hats"),
    ("取引先からの値上げ要求を受け入れるべきか判断したい", "six_hats"),
    ("新入社員の在宅勤務を正式に許可するかどうかを決裁したい", "six_hats"),
    ("競合買収の提案について役員会で採決する前に整理したい", "six_hats"),
    ("バッテリーを大容量にすると重くなってしまい、携帯性が落ちる", "triz"),
    ("橋の強度を上げようとすると建設コストが跳ね上がってしまう", "triz"),
    ("処理速度を上げるとサーバーコストが増えてしまうジレンマがある", "triz"),
    ("梱包を頑丈にすると開けにくくなってしまう", "triz"),
    ("実店舗は接客が丁寧であるべきという業界の常識を疑いたい", "reversal"),
    ("勤務時間は9時から18時が当たり前という前提を覆したい", "reversal"),
    ("レストランは料理を美味しくすることが最優先という思い込みを疑いたい", "reversal"),
    ("新商品のキャッチコピーを何十個も考えたが全部似たり寄ったりでマンネリ化している", "random"),
    ("デザイン案が行き詰まっていて、いつもの発想しか出てこない", "random"),
    ("カスタマーサポートの対応フローを見直して非効率をなくしたい", "osborn_checklist"),
    ("工場の在庫管理プロセスを棚卸しして改善点を洗い出したい", "osborn_checklist"),
    ("採用面接プロセスを総点検したい", "osborn_checklist"),
    ("フィットネスアプリの新機能を考えたい", "scamper"),
    ("既存の弁当宅配サービスを改良して売上を伸ばしたい", "scamper"),
    ("文房具の新商品ラインナップを広げたい", "scamper"),
    ("なぜ自分はこの会社で働き続けたいのか、本当の理由を確かめたい", "socratic"),
    ("この事業戦略が正しいという自分の信念を批判的思考で検証したい", "socratic"),
    ("反対意見を無視している自分に気づいた。前提を問い直したい", "socratic"),
]


@pytest.mark.parametrize("text,expected_method_id", REALISTIC_CASES)
def test_realistic_phrasing_selects_expected_method(text, expected_method_id):
    result = select_methods(text)
    assert result[0].method.id == expected_method_id
    assert result[0].score > 0


# 動詞の活用形(辞書形・連用形・て形)によってキーワードが拾えなくなる
# 語幹バグの回帰テスト。「行き詰まり」→「行き詰まって」で一度見つかった
# クラスのバグが、他の動詞終わりキーワードにも潜んでいないかを確認する。
CONJUGATION_CASES = [
    ("この業界の常識を疑いたい", "reversal"),  # 常識を疑う -> 連用形+たい
    ("当たり前を逆に考えたいと思っている", "reversal"),  # 逆に考える -> 連用形+たい
    ("従来のやり方を覆したい新しい打ち手が欲しい", "reversal"),  # 覆す -> 連用形+たい
    ("自分が正しいと思い込んでいる前提に気づきたい", "reversal"),  # 思い込む -> て形(音便)
    ("この意思決定の前提を問い直したい", "socratic"),  # 問い直す -> 連用形+たい
]


@pytest.mark.parametrize("text,expected_method_id", CONJUGATION_CASES)
def test_verb_conjugation_variants_still_match(text, expected_method_id):
    result = select_methods(text)
    assert result[0].method.id == expected_method_id
    assert result[0].score > 0


DISTRACTOR_CASES = [
    "来月の家族旅行の計画を立てたい",
    "猫の名前を考えたい",
    "資格試験の勉強スケジュールを立てたい",
    "誕生日プレゼントを何にするか悩んでいる",
    "明日の夕食のメニューを決めたい",
    "休日の過ごし方を考えたい",
]


@pytest.mark.parametrize("text", DISTRACTOR_CASES)
def test_unrelated_topics_do_not_false_positive(text):
    """どの発想法とも関連しないお題では、スコア0のフォールバックになるべき。

    (=いずれかの発想法の語句抽出が緩すぎて誤ヒットしていないことの確認)
    """
    from idea_adviser.selector import score_methods

    ranked = score_methods(text)
    assert all(r.score == 0 for r in ranked)
