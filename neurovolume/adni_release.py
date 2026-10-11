"""Prepare the reviewed 09Oct2026 ADNI export; never train or publish records.

Uses actual downloaded dictionary definitions and FreeSurfer 7.4.1 only. Source
DOB is month/year despite dictionary date metadata; age is explicitly approximate.
"""
import argparse
import hashlib
import json
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from .adni_import import run
from .privacy import private_output


def prepare_release(raw_dir, output):
    raw_dir, output = Path(raw_dir), private_output(output)
    names = {k: raw_dir / f"{k}_09Oct2026.csv" for k in ["DATADIC", "CDR", "MMSE", "PTDEMOG", "UCSFFSX7", "ROSTER"]}
    raw = {key: pd.read_csv(path, dtype={"RID": str}, low_memory=False) for key, path in names.items()}
    dictionary = raw["DATADIC"]
    definitions = [("CDR", "CDGLOBAL", "Global CDR", None), ("CDR", "VISDATE", "Registry", None),
                   ("MMSE", "MMSCORE", "MMSE", None), ("PTDEMOG", "PTDOB", "Date of Birth", None),
                   ("UCSFFSX7", "EXAMDATE", "image was collected", None),
                   ("UCSFFSX7", "ST29SV", "LeftHippocampus", "mm3"),
                   ("UCSFFSX7", "ST88SV", "RightHippocampus", "mm3"),
                   ("UCSFFSX7", "ST10CV", "Icv", "mm3"),
                   ("UCSFFSX7", "STATUS", "QC and finalized", None)]
    for table, field, text, unit in definitions:
        found = dictionary[(dictionary.TBLNAME == table) & (dictionary.FLDNAME == field)]
        if found.empty or not found.TEXT.str.contains(text, case=False, regex=False, na=False).any() or (unit and not found.UNITS.eq(unit).all()):
            raise ValueError("Source dictionary differs from reviewed mapping: " + table + "." + field)
    receipts = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in names.items()}
    counts = {}
    cleaned = {}
    for key, date in [("CDR", "VISDATE"), ("MMSE", "VISDATE"), ("PTDEMOG", "VISDATE"), ("UCSFFSX7", "EXAMDATE")]:
        frame = raw[key].copy()
        counts[key] = {"raw_rows": len(frame)}
        if frame.RID.isna().any(): raise ValueError("Missing RID in " + key)
        parsed = pd.to_datetime(frame[date], format="%Y-%m-%d", errors="coerce")
        counts[key]["unavailable_date_rows"] = int(parsed.isna().sum())
        frame = frame[parsed.notna()].copy()
        frame[date] = parsed[parsed.notna()]
        if "HAS_QC_ERROR" in frame:
            flagged = frame.HAS_QC_ERROR.eq(1)
            counts[key]["clinical_qc_error_rows"] = int(flagged.sum())
            frame = frame[~flagged].copy()
        cleaned[key] = frame
    cdr = cleaned["CDR"]
    counts["CDR"]["missing_score_rows"] = int(cdr.CDGLOBAL.isna().sum() + cdr.CDGLOBAL.eq(-1).sum())
    cdr = cdr[cdr.CDGLOBAL.notna() & ~cdr.CDGLOBAL.eq(-1)].copy()
    if not cdr.CDGLOBAL.isin([0, .5, 1, 2, 3]).all(): raise ValueError("Unexpected CDR code")
    # An ambiguous same-day outcome excludes the participant, rather than guessing.
    conflicts = cdr.groupby(["RID", "VISDATE"]).CDGLOBAL.nunique()
    conflict_ids = set(conflicts[conflicts > 1].index.get_level_values(0))
    counts["CDR"]["conflicting_participants_excluded"] = len(conflict_ids)
    cdr = cdr[~cdr.RID.isin(conflict_ids)]
    counts["CDR"]["identical_same_day_rows_collapsed"] = int(cdr.duplicated(["RID", "VISDATE"]).sum())
    cdr = cdr.drop_duplicates(["RID", "VISDATE"]).sort_values(["RID", "VISDATE"])
    mmse = cleaned["MMSE"].copy()
    mmse.loc[mmse.MMSCORE.eq(-1) | mmse.DONE.eq(0), "MMSCORE"] = np.nan
    observed = mmse.MMSCORE.dropna()
    if not observed.between(0, 30).all(): raise ValueError("Unexpected MMSE code")
    conflicts = mmse.groupby(["RID", "VISDATE"]).MMSCORE.nunique(dropna=False)
    ambiguous = set(conflicts[conflicts > 1].index)
    # Conflicting same-day cognitive scores become missing, preserving timing.
    idx = pd.MultiIndex.from_frame(mmse[["RID", "VISDATE"]])
    mmse.loc[idx.isin(ambiguous), "MMSCORE"] = np.nan
    counts["MMSE"]["conflicting_same_day_scores_made_missing"] = len(ambiguous)
    counts["MMSE"]["same_day_rows_collapsed"] = int(mmse.duplicated(["RID", "VISDATE"]).sum())
    mmse = mmse.drop_duplicates(["RID", "VISDATE"])
    mri = cleaned["UCSFFSX7"]
    eligible = mri.STATUS.eq("complete") & mri.OVERALLQC.eq("Pass") & mri.HIPPOQC.eq("Pass") & mri.FSVER.astype(str).eq("7.4.1")
    counts["UCSFFSX7"]["strict_qc_single_version_rows"] = int(eligible.sum())
    mri = mri[eligible].copy()
    # Resolve same-date passing scans by smallest IMAGEUID, a predeclared tie rule.
    mri["image_order"] = pd.to_numeric(mri.IMAGEUID, errors="raise")
    mri["run_order"] = pd.to_datetime(mri.RUNDATE, format="%Y-%m-%d", errors="raise")
    mri = mri.sort_values(["RID", "EXAMDATE", "image_order", "run_order"], ascending=[True, True, True, False])
    counts["UCSFFSX7"]["same_date_passing_rows_collapsed"] = int(mri.duplicated(["RID", "EXAMDATE"]).sum())
    mri = mri.drop_duplicates(["RID", "EXAMDATE"])
    demo = cleaned["PTDEMOG"].copy()
    dob = pd.to_datetime(demo.PTDOB, format="%m/%Y", errors="coerce")
    counts["PTDEMOG"]["missing_or_non_month_year_dob_rows"] = int(dob.isna().sum())
    demo["birth_month"] = dob
    demo = demo[demo.birth_month.notna()].sort_values(["RID", "VISDATE"])
    age_rows = []
    for participant, visits in cdr.groupby("RID", sort=True):
        date = visits.iloc[0].VISDATE
        source = demo[(demo.RID == participant) & (demo.VISDATE <= date)]
        if source.empty: continue
        # Earliest available demographic record, not a future correction.
        birth = source.iloc[0].birth_month
        midpoint = birth.to_pydatetime() + timedelta(days=(birth.days_in_month - 1) / 2)
        age_rows.append({"RID": participant, "AGE_DATE": date, "AGE": (date - midpoint).days / 365.25})
    age = pd.DataFrame(age_rows, columns=["RID", "AGE_DATE", "AGE"])
    output.mkdir(parents=True, exist_ok=True)
    tables = {"assessments": cdr[["RID", "VISDATE", "CDGLOBAL"]], "cognition": mmse[["RID", "VISDATE", "MMSCORE"]],
              "demographics": age, "mri": mri[["RID", "EXAMDATE", "ST29SV", "ST88SV", "ST10CV", "OVERALLQC"]]}
    maps = {"assessments": {"participant_id": "RID", "assessment_date": "VISDATE", "cdr": "CDGLOBAL"},
            "cognition": {"participant_id": "RID", "assessment_date": "VISDATE", "mmse": "MMSCORE"},
            "demographics": {"participant_id": "RID", "age_date": "AGE_DATE", "age": "AGE"},
            "mri": {"participant_id": "RID", "mri_date": "EXAMDATE", "left_hippocampus_mm3": "ST29SV", "right_hippocampus_mm3": "ST88SV", "icv_mm3": "ST10CV", "qc": "OVERALLQC"}}
    config = {"processing": "cross-sectional", "processing_version": "UCSFFSX7 FreeSurfer 7.4.1; 09Oct2026 export", "volume_unit": "mm3"}
    for role, frame in tables.items():
        frame.to_csv(output / (role + ".csv"), index=False, date_format="%Y-%m-%d")
        config[role] = {"path": role + ".csv", "columns": maps[role], "date_format": "%Y-%m-%d",
                        "dictionary_path": str(names["DATADIC"].resolve()), "dictionary_sha256": receipts["DATADIC"]}
    config["mri"].update({"qc_pass_values": ["Pass"], "qc_fail_values": ["Fail"]})
    (output / "mapping.json").write_text(json.dumps(config, indent=2))
    notes = {"raw_checksums": receipts, "cleaning": counts,
             "age": "Approximate age from midpoint of source month/year of birth; up to about half-month uncertainty. No exact birthday inferred.",
             "clinical_dates": "VISDATE is assessment date where present, otherwise registry date per phase dictionary; not universally exact assessment dates.",
             "qc": "Only STATUS complete, OVERALLQC Pass, HIPPOQC Pass, FSVER 7.4.1; exclude partial/not-final and regional salvage.",
             "methods": "2014 methods PDF provides historical QC definitions; it is not a full FreeSurfer 7.4.1 methods specification.",
             "status": "Dictionary-mapped feasibility audit; no training or public disclosure authorized by this command."}
    (output / "source-review.json").write_text(json.dumps(notes, indent=2))
    run(output / "mapping.json", output / "canonical")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", default="private/adni/raw")
    parser.add_argument("--output", default="private/adni/prepared")
    args = parser.parse_args()
    prepare_release(args.raw, args.output)
