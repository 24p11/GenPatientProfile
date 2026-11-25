from pathlib import Path

import polars as pl
import pytest

from fictomed.base import BasePipeline
from fictomed.sites.aphp import prompt
from fictomed.sites.aphp.scenario import format_aphp_scenario


class _Pipeline(BasePipeline):
    def check_data(self):
        pass

    def load_data(self):
        return {}

    def get_fictive(self, data, **kwargs):
        return pl.DataFrame()

    def get_scenario(self, df):
        return df


def _stub_prompt_builders(monkeypatch):
    monkeypatch.setattr(prompt, "make_user_prompt", lambda *_: "USER")
    monkeypatch.setattr(prompt, "load_prefix", lambda *_: "PREFIX")


def test_one_stage_is_the_default_and_keeps_historical_columns(monkeypatch):
    _stub_prompt_builders(monkeypatch)
    monkeypatch.setattr(
        prompt,
        "load_system_prompt",
        lambda name, **_: f"SYSTEM:{name}",
    )
    df = pl.DataFrame({"template_name": ["medical_inpatient.txt"]})

    result = format_aphp_scenario(df, frozenset(), {})

    assert _Pipeline({}).prompt_workflow == "one_stage"
    assert result["user_prompt"].to_list() == ["USER"]
    assert result["system_prompt"].to_list() == ["SYSTEM:medical_inpatient.txt"]
    assert result["prefix"].to_list() == ["PREFIX"]
    assert result["prefix_len"].to_list() == [6]
    assert "summary_system_prompt" not in result.columns
    assert "final_system_prompt" not in result.columns


def test_two_stage_builds_only_two_stage_prompt_columns(monkeypatch):
    _stub_prompt_builders(monkeypatch)
    monkeypatch.setattr(
        prompt,
        "load_system_prompt",
        lambda name, stage=None, **_: f"{stage}:{name}",
    )
    df = pl.DataFrame({"template_name": ["medical_inpatient.txt"]})

    result = format_aphp_scenario(
        df,
        frozenset(),
        {},
        prompt_workflow="two_stage",
        prompt_set="old",
    )

    assert result["user_prompt"].to_list() == ["USER"]
    assert result["summary_system_prompt"].to_list() == [
        "summary:medical_inpatient.txt"
    ]
    assert result["summary_prefix"].to_list() == [""]
    assert result["final_system_prompt"].to_list() == [
        "final:medical_inpatient.txt"
    ]
    assert result["final_prefix"].to_list() == ["PREFIX"]
    assert "system_prompt" not in result.columns
    assert "prefix" not in result.columns
    assert "prefix_len" not in result.columns


def test_two_stage_templates_are_loaded_from_stage_directories():
    summary = prompt.load_system_prompt(
        "medical_inpatient.txt", stage="summary", prompt_set="old"
    )
    final = prompt.load_system_prompt(
        "medical_inpatient.txt", stage="final", prompt_set="old"
    )

    assert "résumé clinique contrôlé" in summary
    assert "documents médicaux finaux" in final


@pytest.mark.parametrize(
    "template_name",
    sorted(
        path.name
        for path in (
            Path(prompt.__file__).resolve().parent / "templates" / "old" / "one_stage"
        ).glob("*.txt")
    ),
)
def test_every_historical_template_has_summary_and_final_variants(template_name):
    summary = prompt.load_system_prompt(
        template_name, stage="summary", prompt_set="old"
    )
    final = prompt.load_system_prompt(template_name, stage="final", prompt_set="old")

    assert summary.strip()
    assert final.strip()


def test_make_final_user_prompt_appends_summary():
    result = prompt.make_final_user_prompt("SCÉNARIO\n", "  RÉSUMÉ  ")

    assert result.startswith("SCÉNARIO\n\n")
    assert result.endswith("**RÉSUMÉ CLINIQUE CONTRÔLÉ :**\nRÉSUMÉ\n")


def test_invalid_workflow_is_rejected():
    with pytest.raises(ValueError, match="prompt_workflow"):
        _Pipeline({}, prompt_workflow="invalid")


def test_invalid_template_stage_is_rejected():
    with pytest.raises(ValueError, match="stage"):
        prompt.load_system_prompt("medical_inpatient.txt", stage="invalid")
