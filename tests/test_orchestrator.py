from idea_adviser.generator import TemplateGenerator
from idea_adviser.orchestrator import Orchestrator
from idea_adviser.report import to_markdown


def test_orchestrator_runs_full_method_for_topic():
    orchestrator = Orchestrator(generator=TemplateGenerator())
    result = orchestrator.run("新商品のアイデアを新機能の観点で改良して考えたい")

    assert result.topic
    assert len(result.runs) == 1
    run = result.primary
    assert run.method.id == "scamper"
    assert len(run.steps) == len(run.method.steps)
    for step in run.steps:
        assert step.ideas


def test_orchestrator_forced_method():
    orchestrator = Orchestrator()
    result = orchestrator.run("何かのお題", method_id="six_hats")
    assert result.primary.method.id == "six_hats"
    assert len(result.primary.steps) == 6


def test_orchestrator_top_k_multiple_methods():
    orchestrator = Orchestrator()
    text = "新商品の新機能アイデアを、既存製品を改良する形で幅広く出したい。"
    result = orchestrator.run(text, top_k=2)
    assert len(result.runs) == 2


def test_orchestrator_rejects_empty_topic():
    orchestrator = Orchestrator()
    try:
        orchestrator.run("   ")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for empty topic")


def test_report_contains_topic_and_method_name():
    orchestrator = Orchestrator()
    result = orchestrator.run("新商品の新機能アイデアを改良して考えたい")
    report = to_markdown(result)
    assert result.topic in report
    assert result.primary.method.name_ja in report
    for step in result.primary.steps:
        assert step.step_title in report
