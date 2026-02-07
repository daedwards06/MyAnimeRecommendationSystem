import importlib


def test_should_relax_off_type_penalty_neural_high_sim(monkeypatch):
    monkeypatch.setenv("HIGH_SIM_OVERRIDE_THRESHOLD", "0.60")
    monkeypatch.setenv("HIGH_SIM_OVERRIDE_MODE", "relax_off_type_penalty")

    import src.app.constants as constants

    importlib.reload(constants)

    import src.app.stage2_overrides as overrides

    importlib.reload(overrides)

    assert overrides.should_relax_off_type_penalty(neural_sim=0.59, semantic_mode="neural") is False
    assert overrides.should_relax_off_type_penalty(neural_sim=0.60, semantic_mode="neural") is True
    assert overrides.should_relax_off_type_penalty(neural_sim=0.90, semantic_mode="neural") is True

    assert overrides.should_relax_off_type_penalty(neural_sim=0.90, semantic_mode="tfidf") is False
    assert overrides.should_relax_off_type_penalty(neural_sim=0.90, semantic_mode="embeddings") is False
    assert overrides.should_relax_off_type_penalty(neural_sim=0.90, semantic_mode="") is False

    assert overrides.should_relax_off_type_penalty(neural_sim=0.90, semantic_mode="neural", browse_mode=True) is False


def test_relax_off_type_penalty_zeroes_only_negative(monkeypatch):
    monkeypatch.setenv("HIGH_SIM_OVERRIDE_THRESHOLD", "0.60")
    monkeypatch.setenv("HIGH_SIM_OVERRIDE_MODE", "relax_off_type_penalty")

    import src.app.constants as constants

    importlib.reload(constants)

    import src.app.stage2_overrides as overrides

    importlib.reload(overrides)

    assert overrides.relax_off_type_penalty(penalty=-0.01, neural_sim=0.60, semantic_mode="neural") == 0.0
    assert overrides.relax_off_type_penalty(penalty=-0.50, neural_sim=0.95, semantic_mode="neural") == 0.0
    assert overrides.relax_off_type_penalty(penalty=0.0, neural_sim=0.95, semantic_mode="neural") == 0.0
    assert overrides.relax_off_type_penalty(penalty=-0.01, neural_sim=0.59, semantic_mode="neural") == -0.01
