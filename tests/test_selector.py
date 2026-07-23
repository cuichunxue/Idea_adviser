from idea_adviser.selector import select_methods, score_methods, DEFAULT_FALLBACK_METHOD_ID


def test_six_hats_selected_for_decision_making():
    text = "新しい提案について、チームで多角的に評価し賛否を整理して意思決定したい。"
    result = select_methods(text)
    assert result[0].method.id == "six_hats"
    assert result[0].score > 0


def test_triz_selected_for_technical_contradiction():
    text = "製品設計で強度を上げるとコストが増えるという技術的な矛盾(トレードオフ)を解消したい。"
    result = select_methods(text)
    assert result[0].method.id == "triz"


def test_reversal_selected_for_fixed_mindset():
    text = "業界の当たり前や固定観念を疑い、常識を疑ってブレイクスルーを起こしたい。"
    result = select_methods(text)
    assert result[0].method.id == "reversal"


def test_random_selected_for_stuck_brainstorm():
    text = "アイデアがマンネリ化して行き詰まっている。ランダムな刺激で突破口が欲しい。"
    result = select_methods(text)
    assert result[0].method.id == "random"


def test_osborn_selected_for_comprehensive_review():
    text = "既存の業務プロセスを見直して、漏れなく網羅的に改善点をチェックリストで洗い出したい。"
    result = select_methods(text)
    assert result[0].method.id == "osborn_checklist"


def test_scamper_selected_for_new_feature_ideation():
    text = "新商品の新機能アイデアを、既存製品を改良する形で幅広く出したい。"
    result = select_methods(text)
    assert result[0].method.id == "scamper"


def test_socratic_selected_for_introspection():
    text = "自分の信念や主張の前提を批判的思考で問い直し、内省して思考を明確化したい。"
    result = select_methods(text)
    assert result[0].method.id == "socratic"


def test_fallback_when_no_signal():
    text = "asdfgh qwerty"
    result = select_methods(text)
    assert result[0].method.id == DEFAULT_FALLBACK_METHOD_ID
    assert result[0].score == 0
    assert result[0].reason


def test_forced_method_overrides_scoring():
    text = "多角的に評価したい提案がある。"
    result = select_methods(text, method_id="triz")
    assert len(result) == 1
    assert result[0].method.id == "triz"
    assert result[0].forced is True


def test_top_k_returns_multiple_methods():
    text = "新商品の新機能アイデアを、既存製品を改良する形で幅広く出したい。"
    result = select_methods(text, top_k=2)
    assert len(result) == 2


def test_score_methods_returns_all_methods_sorted():
    text = "新商品の新機能アイデア"
    scores = score_methods(text)
    assert len(scores) == len(scores)  # sanity
    assert scores == sorted(scores, key=lambda r: (-r.score, r.method.priority))
