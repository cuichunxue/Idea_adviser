from idea_adviser.methods import METHODS


def test_all_methods_have_required_ids():
    expected = {
        "six_hats",
        "triz",
        "reversal",
        "random",
        "osborn_checklist",
        "scamper",
        "socratic",
    }
    assert set(METHODS) == expected


def test_every_method_has_steps_and_benefits():
    for method in METHODS.values():
        assert method.steps, f"{method.id} has no steps"
        assert method.benefits, f"{method.id} has no benefits"
        assert method.keywords, f"{method.id} has no keywords"


def test_step_render_substitutes_topic():
    method = METHODS["scamper"]
    step = method.steps[0]
    rendered = step.render("電動自転車")
    assert "電動自転車" in rendered
    assert "{topic}" not in rendered


def test_osborn_checklist_has_nine_steps():
    assert len(METHODS["osborn_checklist"].steps) == 9


def test_six_hats_has_six_steps():
    assert len(METHODS["six_hats"].steps) == 6
