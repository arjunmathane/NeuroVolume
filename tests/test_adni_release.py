"""Invented exports exercise source cleaning without redistributing ADNI records."""
import json
import pandas as pd
import pytest
from neurovolume.adni_release import prepare_release


def test_reviewed_export_cleaning(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw = tmp_path / "private/raw"
    raw.mkdir(parents=True)
    definitions = [
        ("CDR", "CDGLOBAL", "Global CDR", None),
        ("CDR", "VISDATE", "Registry date", None),
        ("MMSE", "MMSCORE", "MMSE", None),
        ("PTDEMOG", "PTDOB", "Date of Birth", None),
        ("UCSFFSX7", "EXAMDATE", "When the image was collected", None),
        ("UCSFFSX7", "ST29SV", "LeftHippocampus", "mm3"),
        ("UCSFFSX7", "ST88SV", "RightHippocampus", "mm3"),
        ("UCSFFSX7", "ST10CV", "Icv", "mm3"),
        ("UCSFFSX7", "STATUS", "QC and finalized", None)]
    def save(name, rows):
        pd.DataFrame(rows).to_csv(raw / f"{name}_09Oct2026.csv", index=False)
    save("DATADIC", [dict(zip(["TBLNAME", "FLDNAME", "TEXT", "UNITS"], d)) for d in definitions])
    save("ROSTER", [{"RID": "001"}])
    cdr = [{"RID": rid, "VISDATE": date, "CDGLOBAL": score, "HAS_QC_ERROR": 0}
           for rid, date, score in [("001", "2020-01-01", 0), ("001", "2021-01-01", .5),
                                    ("001", "2021-01-01", .5), ("002", "2020-01-01", 0),
                                    ("002", "2020-01-01", .5), ("003", "2020-01-01", 0)]]
    save("CDR", cdr)
    save("MMSE", [{"RID": "001", "VISDATE": "2019-12-31", "MMSCORE": score, "DONE": 1}
                  for score in [28, 29]])
    save("PTDEMOG", [{"RID": rid, "VISDATE": date, "PTDOB": "01/1950"}
                     for rid, date in [("001", "2019-12-01"), ("003", "2020-02-01")]])
    mri = {"RID": "001", "EXAMDATE": "2019-12-31", "RUNDATE": "2020-02-01",
           "STATUS": "complete", "OVERALLQC": "Pass", "HIPPOQC": "Pass", "FSVER": "7.4.1",
           "ST29SV": 3000, "ST88SV": 3100, "ST10CV": 1500000, "IMAGEUID": 10}
    save("UCSFFSX7", [mri, {**mri, "IMAGEUID": 11, "ST29SV": 9000},
                       {**mri, "RID": "003", "OVERALLQC": "Partial"}])
    out = tmp_path / "private/prepared"
    prepare_release(raw, out)
    review = json.loads((out / "source-review.json").read_text())
    assert review["cleaning"]["CDR"]["conflicting_participants_excluded"] == 1
    assert review["cleaning"]["CDR"]["identical_same_day_rows_collapsed"] == 1
    assert review["cleaning"]["MMSE"]["conflicting_same_day_scores_made_missing"] == 1
    assert review["cleaning"]["UCSFFSX7"]["same_date_passing_rows_collapsed"] == 1
    cohort = pd.read_csv(out / "canonical/cohort.csv", dtype={"participant_id": str})
    assert cohort.participant_id.tolist() == ["001"]
    assert cohort.event.tolist() == [1]
    assert cohort.mmse.isna().all()
    assert cohort.hippocampus_icv_ratio.iloc[0] == pytest.approx(6100 / 1500000)
    assert len(pd.read_csv(out / "demographics.csv")) == 1  # future DOB is excluded
