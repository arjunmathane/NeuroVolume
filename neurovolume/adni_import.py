"""Dictionary-configured research importer; no verified ADNI mapping is bundled.

Mappings must reference actual downloaded dictionaries. Synthetic tests verify
mechanics only. Outputs and source inventory remain in ignored private storage.
"""
import argparse
import hashlib
import json
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .longitudinal import prepare
from .privacy import private_output

FIELDS = {
    "assessments": {"participant_id", "assessment_date", "cdr"},
    "cognition": {"participant_id", "assessment_date", "mmse"},
    "demographics": {"participant_id", "age_date", "age"},
    "mri": {"participant_id", "mri_date", "left_hippocampus_mm3", "right_hippocampus_mm3", "icv_mm3", "qc"},
}


def mapped(frame, role, spec):
    mapping = spec["columns"]
    if set(mapping) != FIELDS[role] or len(set(mapping.values())) != len(mapping) or not set(mapping.values()) <= set(frame):
        raise ValueError("Missing or unexpected mapping/source columns: " + role)
    result = frame[list(mapping.values())].rename(columns={v: k for k, v in mapping.items()}).copy()
    if result.participant_id.isna().any() or result.participant_id.astype(str).str.strip().eq("").any():
        raise ValueError("Missing identifier: " + role)
    result["participant_id"] = result.participant_id.astype(str).str.strip()
    # Missing codes are field-specific. Do not globally erase values (e.g., CDR 0).
    for field, codes in spec.get("missing_codes", {}).items():
        if field not in result or field == "participant_id" or field.endswith("date"):
            raise ValueError("Invalid missing-code mapping: " + field)
        result[field] = result[field].replace(codes, np.nan)
    for column in [c for c in result if c.endswith("date")]:
        result[column] = pd.to_datetime(result[column], format=spec["date_format"], errors="raise")
        if result[column].isna().any():
            raise ValueError("Missing source date: " + role)
    for field in set(result) - {"participant_id", "qc"} - {c for c in result if c.endswith("date")}:
        result[field] = pd.to_numeric(result[field], errors="raise")
        observed = result[field].dropna()
        if not np.isfinite(observed).all():
            raise ValueError("Nonfinite source measurement: " + field)
    keys = ["participant_id"] + [c for c in result if c.endswith("date")]
    if result.duplicated(keys).any():
        raise ValueError("Ambiguous duplicate source records: " + role)
    return result


def adapt(tables, config):
    if config.get("processing") != "cross-sectional" or config.get("volume_unit") != "mm3":
        raise ValueError("Require one cross-sectional processing version and verified mm3 units.")
    if not config.get("processing_version"):
        raise ValueError("Specify one reviewed processing version.")
    data = {role: mapped(tables[role], role, config[role]) for role in FIELDS}
    visits = data["assessments"]
    # Missing CDR is not an unimpaired observation and does not set the baseline.
    missing_cdr = int(visits.cdr.isna().sum())
    visits = visits.dropna(subset=["cdr"]).sort_values(["participant_id", "assessment_date"])
    if not visits.cdr.isin([0, .5, 1, 2, 3]).all():
        raise ValueError("Unrecognized CDR value; review dictionary missing codes.")
    cognition = data["cognition"]
    if ((cognition.mmse.dropna() < 0) | (cognition.mmse.dropna() > 30)).any():
        raise ValueError("Unrecognized MMSE value; review dictionary missing codes.")
    demos = data["demographics"]
    if demos.participant_id.duplicated().any():
        raise ValueError("Demographic reference age must have one source row per participant.")
    if demos.age.isna().any() or not demos.age.between(18, 120).all():
        raise ValueError("Require valid source reference age.")
    mri = data["mri"]
    volume_fields = ["left_hippocampus_mm3", "right_hippocampus_mm3", "icv_mm3"]
    for field in volume_fields:
        x = mri[field].dropna()
        limits = (100000, 3000000) if field == "icv_mm3" else (1, 15000)
        if not x.between(*limits).all():
            raise ValueError("MRI unit/range mismatch: " + field)
    for field in volume_fields[:2]:
        if (mri[field] > mri.icv_mm3).any():
            raise ValueError("Regional volume exceeds ICV.")
    qc_spec = config["mri"]
    if not qc_spec.get("qc_pass_values") or not qc_spec.get("qc_fail_values"):
        raise ValueError("Specify both reviewed QC pass and fail values.")
    pass_values, fail_values = qc_spec["qc_pass_values"], qc_spec["qc_fail_values"]
    if set(pass_values) & set(fail_values):
        raise ValueError("QC pass/fail definitions overlap.")
    if not mri.qc.dropna().isin(pass_values + fail_values).all():
        raise ValueError("Unknown QC category; do not silently reinterpret it.")
    mri["passed"] = mri.qc.isin(pass_values)
    rows = []
    exclusions = {"baseline_impaired": 0, "no_reference_age": 0, "reference_age_after_baseline": 0,
                  "no_prior_qc_mri": 0}
    mmse_missing = 0
    strategy = config.get("baseline_strategy", "first_observed")
    if strategy not in {"first_observed", "first_eligible"}:
        raise ValueError("Unknown baseline strategy.")
    for participant, g in visits.groupby("participant_id", sort=True):
        # Earliest observed CDR assessment, never an outcome-dependent later visit.
        baseline = g.iloc[0]
        if baseline.cdr != 0:
            exclusions["baseline_impaired"] += 1
            continue
        if strategy == "first_eligible":
            candidates = []
            for _, assessment in g.iterrows():
                if assessment.cdr > 0:
                    break  # Never choose a baseline after recorded impairment.
                lag = (assessment.assessment_date - mri.mri_date).dt.days
                if ((mri.participant_id == participant) & mri.passed & lag.between(0, 180)).any():
                    candidates.append(assessment)
                    break
            if not candidates:
                exclusions["no_prior_qc_mri"] += 1
                continue
            baseline = candidates[0]
        demo = demos[demos.participant_id == participant]
        if demo.empty:
            exclusions["no_reference_age"] += 1
            continue
        demo = demo.iloc[0]
        if demo.age_date > baseline.assessment_date:
            exclusions["reference_age_after_baseline"] += 1
            continue
        scans = mri[(mri.participant_id == participant) & mri.passed &
                    (mri.mri_date <= baseline.assessment_date) &
                    (mri.mri_date >= baseline.assessment_date.to_pydatetime() - timedelta(days=180))]
        if scans.empty:
            exclusions["no_prior_qc_mri"] += 1
            continue
        scan = scans.sort_values("mri_date").iloc[-1]
        cog = cognition[(cognition.participant_id == participant) &
                        (cognition.assessment_date <= baseline.assessment_date) &
                        (cognition.assessment_date >= baseline.assessment_date.to_pydatetime() - timedelta(days=30))]
        # Most recent assessment stays missing if its score is missing; no future fill.
        mmse = cog.sort_values("assessment_date").iloc[-1].mmse if len(cog) else np.nan
        mmse_missing += int(pd.isna(mmse))
        hippo = scan.left_hippocampus_mm3 + scan.right_hippocampus_mm3
        rows.append({"participant_id": participant, "baseline_date": baseline.assessment_date,
                     "mri_date": scan.mri_date, "age": demo.age + (baseline.assessment_date - demo.age_date).days / 365.25,
                     "mmse": mmse, "hippocampus_mm3": hippo, "icv_mm3": scan.icv_mm3, "mri_qc_pass": 1})
    columns = ["participant_id", "baseline_date", "mri_date", "age", "mmse", "hippocampus_mm3", "icv_mm3", "mri_qc_pass"]
    baseline = pd.DataFrame(rows, columns=columns)
    selected_visits = visits[visits.participant_id.isin(baseline.participant_id)].copy()
    report = {"source_rows": {key: len(value) for key, value in tables.items()},
              "participants_with_observed_cdr": int(visits.participant_id.nunique()),
              "missing_cdr_rows_not_used": missing_cdr, "baseline_candidates": len(baseline),
              "exclusions": exclusions, "missing_selected_mmse": mmse_missing,
              "baseline_rule": "Earliest observed CDR assessment; never substitute a later eligible visit." if strategy == "first_observed" else "First MRI-eligible zero-CDR assessment; exclude any prior recorded impairment; observation starts at that assessment.",
              "mri_rule": "Most recent passing cross-sectional acquisition on/before baseline within 180 days.",
              "cognition_rule": "Most recent assessment on/before baseline within 30 days; preserve missing score.",
              "processing_version": config["processing_version"], "status": "Import audit; no model trained."}
    if report["participants_with_observed_cdr"] != len(baseline) + sum(exclusions.values()):
        raise AssertionError("Participant accounting failed.")
    return baseline, selected_visits, report


def run(config_path, output):
    config_path, output = Path(config_path).resolve(), private_output(output)
    config = json.loads(config_path.read_text())
    sources, checksums = {}, {}
    for role in FIELDS:
        spec = config[role]
        for item in ["path", "dictionary_path", "dictionary_sha256"]:
            if not spec.get(item): raise ValueError("Require a source and dictionary receipt: " + role)
        dictionary = (config_path.parent / spec["dictionary_path"]).resolve()
        digest = hashlib.sha256(dictionary.read_bytes()).hexdigest()
        if digest != spec["dictionary_sha256"]:
            raise ValueError("Dictionary checksum mismatch: " + role)
        path = (config_path.parent / spec["path"]).resolve()
        sources[role] = pd.read_csv(path, dtype={spec["columns"]["participant_id"]: str}, low_memory=False)
        checksums[role] = {"source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "dictionary_sha256": digest}
    baseline, visits, audit = adapt(sources, config)
    if baseline.empty:
        raise ValueError("No baseline candidates: inspect eligibility before training.")
    cohort, eligibility = prepare(baseline, visits)
    audit.update({"checksums": checksums, "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(), "canonical_audit": eligibility})
    output.mkdir(parents=True, exist_ok=True)
    baseline.to_csv(output / "baseline.csv", index=False, date_format="%Y-%m-%d")
    visits.to_csv(output / "visits.csv", index=False, date_format="%Y-%m-%d")
    cohort.to_csv(output / "cohort.csv", index=False)
    (output / "audit.json").write_text(json.dumps(audit, indent=2, allow_nan=False))
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", default="private/adni/canonical")
    args = parser.parse_args()
    run(args.config, args.output)
