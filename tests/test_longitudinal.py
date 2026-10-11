from pathlib import Path
import pandas as pd
import pytest
from neurovolume.longitudinal import prepare

ROOT=Path(__file__).resolve().parents[1]
def inputs():
    return (pd.read_csv(ROOT/"examples/longitudinal/baseline.csv"),pd.read_csv(ROOT/"examples/longitudinal/visits.csv"))

def test_intervals_censoring_and_exclusions():
    b,v=inputs(); x,a=prepare(b,v,True);x=x.set_index("participant_id")
    assert a["included"]==4 and a["events"]==2 and a["right_censored"]==2
    assert a["excluded"]["mri_after_baseline"]==1 and a["excluded"]["failed_mri_qc"]==1
    assert x.loc["synthetic_01","last_zero_days"]==366
    assert x.loc["synthetic_01","first_positive_days"]==731
    assert x.loc["synthetic_03","event"]==1 # later reversion does not erase event
    assert x.loc["synthetic_03","first_positive_days"]==182
    assert pd.isna(x.loc["synthetic_02","first_positive_days"])
    assert x.loc["synthetic_02","last_zero_days"]==1096
    assert a["missing_predictors"]["hippocampus_icv_ratio"]==1
    assert sum(a["followup_counts"])==len(x)

@pytest.mark.parametrize("kind",["duplicate_baseline","duplicate_visit","unknown_id","units","missing_date","invalid_cdr"])
def test_reject_malformed_inputs(kind):
    b,v=inputs()
    if kind=="duplicate_baseline": b=pd.concat([b,b.iloc[[0]]])
    if kind=="duplicate_visit": v=pd.concat([v,v.iloc[[0]]])
    if kind=="unknown_id": v.loc[0,"participant_id"]="unknown"
    if kind=="units": b.loc[0,"icv_mm3"]=1400
    if kind=="missing_date": b.loc[0,"baseline_date"]=None
    if kind=="invalid_cdr": v.loc[0,"cdr"]=-1
    with pytest.raises(ValueError): prepare(b,v)

def test_eligibility_boundaries():
    b,v=inputs();b.loc[0,"mri_date"]="2019-01-01"
    v=v[~((v.participant_id=="synthetic_02")&(v.assessment_date=="2020-01-01"))]
    v.loc[(v.participant_id=="synthetic_03")&(v.assessment_date=="2020-01-01"),"cdr"]=.5
    v=v[~((v.participant_id=="synthetic_06")&(v.assessment_date!="2020-01-01"))]
    x,a=prepare(b,v)
    assert x.empty and sum(a["excluded"].values())==len(b)
    for k in ["mri_too_old","no_baseline_assessment","baseline_impaired","no_followup"]:assert a["excluded"][k]==1
