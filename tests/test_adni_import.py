"""Invented records test import mechanics, not a verified ADNI source schema."""
import hashlib
import json
import pandas as pd
import pytest
from neurovolume.adni_import import adapt, run


def fixture():
    tables = {
        "assessments": pd.DataFrame({"ID": ["001", "001", "001", "002", "002"], "DATE": ["2020-01-01", "2021-01-01", "2022-01-01", "2020-01-01", "2021-01-01"], "CDR": [0, 0, .5, 0, 0]}),
        "cognition": pd.DataFrame({"ID": ["001", "001", "002"], "DATE": ["2019-12-20", "2020-01-02", "2020-01-01"], "SCORE": [28, 10, 29]}),
        "demographics": pd.DataFrame({"ID": ["001", "002"], "DATE": ["2020-01-01", "2020-01-01"], "AGE": [75, 76]}),
        "mri": pd.DataFrame({"ID": ["001", "001", "001", "002"], "DATE": ["2019-12-20", "2019-12-25", "2020-01-02", "2020-01-01"], "LEFT": [3000, 9000, 10000, 3200], "RIGHT": [3100, 9000, 10000, 3300], "ICV": [1400000] * 4, "QC": ["Pass", "Fail", "Pass", "Pass"]}),
    }
    columns = {
        "assessments": {"participant_id": "ID", "assessment_date": "DATE", "cdr": "CDR"},
        "cognition": {"participant_id": "ID", "assessment_date": "DATE", "mmse": "SCORE"},
        "demographics": {"participant_id": "ID", "age_date": "DATE", "age": "AGE"},
        "mri": {"participant_id": "ID", "mri_date": "DATE", "left_hippocampus_mm3": "LEFT", "right_hippocampus_mm3": "RIGHT", "icv_mm3": "ICV", "qc": "QC"},
    }
    config = {"processing": "cross-sectional", "processing_version": "SYNTHETIC-TEST-1", "volume_unit": "mm3"}
    for role in tables:
        config[role] = {"columns": columns[role], "date_format": "%Y-%m-%d"}
    config["mri"].update({"qc_pass_values": ["Pass"], "qc_fail_values": ["Fail"]})
    return tables, config


def test_no_future_measurements_and_qc_selection():
    tables, config = fixture()
    baseline, visits, audit = adapt(tables, config)
    p = baseline.set_index("participant_id").loc["001"]
    assert p.mmse == 28  # Future MMSE 10 cannot enter baseline.
    assert p.hippocampus_mm3 == 6100  # Failed or future scans ignored.
    assert p.mri_date == pd.Timestamp("2019-12-20")
    assert audit["baseline_candidates"] == 2
    assert set(visits.participant_id) == {"001", "002"}


def test_preserve_most_recent_missing_score_and_hemisphere():
    tables, config = fixture()
    tables["cognition"].loc[0, "SCORE"] = -4
    tables["mri"].loc[0, "LEFT"] = -4
    config["cognition"]["missing_codes"] = {"mmse": [-4]}
    config["mri"]["missing_codes"] = {"left_hippocampus_mm3": [-4]}
    baseline, _, audit = adapt(tables, config)
    p = baseline.set_index("participant_id").loc["001"]
    assert pd.isna(p.mmse) and pd.isna(p.hippocampus_mm3)
    assert audit["missing_selected_mmse"] == 1


def test_no_rebaseline_after_impairment_or_future_age():
    tables, config = fixture()
    tables["assessments"].loc[0, "CDR"] = .5
    tables["demographics"].loc[1, "DATE"] = "2020-01-02"
    baseline, _, audit = adapt(tables, config)
    assert baseline.empty
    assert audit["exclusions"]["baseline_impaired"] == 1
    assert audit["exclusions"]["reference_age_after_baseline"] == 1


@pytest.mark.parametrize("bad", ["duplicate", "unknown_qc", "qc_overlap", "units", "longitudinal", "sentinel", "reused_column"])
def test_ambiguous_or_unreviewed_sources_rejected(bad):
    tables, config = fixture()
    if bad == "duplicate": tables["mri"] = pd.concat([tables["mri"], tables["mri"].iloc[[0]]])
    if bad == "unknown_qc": tables["mri"].loc[0, "QC"] = "UNREVIEWED"
    if bad == "qc_overlap": config["mri"]["qc_fail_values"] = ["Pass"]
    if bad == "units": tables["mri"]["ICV"] = 1400
    if bad == "longitudinal": config["processing"] = "longitudinal"
    if bad == "sentinel": tables["cognition"].loc[0, "SCORE"] = -4
    if bad == "reused_column": config["mri"]["columns"]["right_hippocampus_mm3"] = "LEFT"
    with pytest.raises(ValueError): adapt(tables, config)


def test_unknown_mri_and_expired_window_not_selected():
    tables, config = fixture()
    tables["mri"].loc[0, "DATE"] = "2019-01-01"
    tables["mri"].loc[3, "QC"] = None
    baseline, _, audit = adapt(tables, config)
    assert baseline.empty
    assert audit["exclusions"]["no_prior_qc_mri"] == 2


def test_first_eligible_baseline_starts_after_mri_without_prior_event():
    tables, config = fixture()
    config["baseline_strategy"] = "first_eligible"
    tables["mri"].loc[0, "DATE"] = "2020-12-20"
    tables["mri"].loc[2, "QC"] = "Fail"
    baseline, _, _ = adapt(tables, config)
    p = baseline.set_index("participant_id").loc["001"]
    assert p.baseline_date == pd.Timestamp("2021-01-01")
    assert pd.isna(p.mmse)  # No eligible contemporaneous cognition; no future fill.
    tables["assessments"].loc[1, "CDR"] = .5
    baseline, _, audit = adapt(tables, config)
    assert "001" not in set(baseline.participant_id)
    assert audit["exclusions"]["no_prior_qc_mri"] == 1


def test_receipts_and_private_outputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tables, config = fixture()
    dictionary = tmp_path / "dictionary.txt"
    dictionary.write_text("Synthetic dictionary for invented test fields; not ADNI definitions.")
    digest = hashlib.sha256(dictionary.read_bytes()).hexdigest()
    for role, frame in tables.items():
        frame.to_csv(tmp_path / (role + ".csv"), index=False)
        config[role].update({"path": role + ".csv", "dictionary_path": dictionary.name, "dictionary_sha256": digest})
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    output = tmp_path / "private/canonical"
    run(path, output)
    cohort = pd.read_csv(output / "cohort.csv", dtype={"participant_id": str})
    assert cohort.participant_id.tolist() == ["001", "002"]
    assert cohort.event.tolist() == [1, 0]
    assert json.loads((output / "audit.json").read_text())["canonical_audit"]["included"] == 2
    with pytest.raises(ValueError, match="private"): run(path, tmp_path / "public")
    dictionary.write_text("Changed dictionary")
    with pytest.raises(ValueError, match="checksum"): run(path, output)
