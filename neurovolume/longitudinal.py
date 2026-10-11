"""Validate canonical longitudinal CSVs and preserve event observation intervals.
No dataset-specific ADNI column mapping or new disease model is implied.
"""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from .privacy import private_output

BASE = {"participant_id", "baseline_date", "mri_date", "age", "mmse", "hippocampus_mm3", "icv_mm3", "mri_qc_pass"}
VISITS = {"participant_id", "assessment_date", "cdr"}

def validate(b, v):
    b=b.copy(); v=v.copy()
    if not BASE <= set(b) or not VISITS <= set(v):
        raise ValueError("Missing canonical columns; see docs/LONGITUDINAL_SCHEMA.md.")
    if b.empty or v.empty: raise ValueError("Both input tables must contain records.")
    for x in (b,v):
        if x.participant_id.isna().any() or x.participant_id.astype(str).str.strip().eq("").any():
            raise ValueError("Participant identifiers cannot be missing.")
        x["participant_id"]=x.participant_id.astype(str)
    if b.participant_id.duplicated().any(): raise ValueError("Duplicate baseline participant rows.")
    if not set(v.participant_id)<=set(b.participant_id): raise ValueError("Visits reference unknown participants.")
    for x, cols in [(b,["baseline_date","mri_date"]),(v,["assessment_date"])]:
        for c in cols:
            x[c]=pd.to_datetime(x[c], format="%Y-%m-%d", errors="raise")
            if x[c].isna().any(): raise ValueError("Dates cannot be missing.")
    if v.duplicated(["participant_id","assessment_date"]).any():
        raise ValueError("Duplicate or conflicting same-day assessments.")
    for c,lo,hi in [("age",18,120),("mmse",0,30),("hippocampus_mm3",0,30000),("icv_mm3",100000,3000000)]:
        b[c]=pd.to_numeric(b[c],errors="raise")
        observed=b[c].dropna()
        if (~np.isfinite(observed)).any() or ((observed<lo)|(observed>hi)).any():
            raise ValueError("Implausible numeric baseline measurement or unit mismatch: "+c)
    if b.age.isna().any(): raise ValueError("Baseline age is required.")
    if (b.hippocampus_mm3.dropna()<=0).any(): raise ValueError("Observed hippocampus volume must be positive.")
    if (b.hippocampus_mm3>b.icv_mm3).any(): raise ValueError("Hippocampus exceeds intracranial volume.")
    if not b.mri_qc_pass.isin([0,1]).all(): raise ValueError("MRI QC must be 0 or 1.")
    v["cdr"]=pd.to_numeric(v.cdr,errors="raise")
    if not v.cdr.isin([0,.5,1,2,3]).all(): raise ValueError("CDR must be observed and valid.")
    return b,v

def prepare(b,v,synthetic=False):
    b,v=validate(b,v)
    excluded={"mri_after_baseline":0,"mri_too_old":0,"failed_mri_qc":0,"no_baseline_assessment":0,"baseline_impaired":0,"no_followup":0}
    rows=[]
    for _,p in b.iterrows():
        lag=(p.baseline_date-p.mri_date).days
        if lag<0: excluded["mri_after_baseline"]+=1;continue
        if lag>180: excluded["mri_too_old"]+=1;continue
        if p.mri_qc_pass!=1: excluded["failed_mri_qc"]+=1;continue
        g=v[v.participant_id==p.participant_id].sort_values("assessment_date")
        base=g[g.assessment_date==p.baseline_date]
        if base.empty: excluded["no_baseline_assessment"]+=1;continue
        if base.iloc[0].cdr!=0: excluded["baseline_impaired"]+=1;continue
        g=g[g.assessment_date>p.baseline_date]
        if g.empty: excluded["no_followup"]+=1;continue
        pos=g[g.cdr>0]
        event=not pos.empty
        end=pos.iloc[0].assessment_date if event else g.iloc[-1].assessment_date
        prior=g[(g.assessment_date<end)&(g.cdr==0)]
        last_zero=prior.iloc[-1].assessment_date if not prior.empty else p.baseline_date
        if not event: last_zero=end
        ratio=p.hippocampus_mm3/p.icv_mm3 if pd.notna(p.hippocampus_mm3) and pd.notna(p.icv_mm3) else np.nan
        rows.append({"participant_id":p.participant_id,"age":p.age,"mmse":p.mmse,
                     "hippocampus_icv_ratio":ratio,"event":int(event),
                     "last_zero_days":(last_zero-p.baseline_date).days,
                     "first_positive_days":(end-p.baseline_date).days if event else np.nan,
                     "followup_days":(end-p.baseline_date).days})
    cols=["participant_id","age","mmse","hippocampus_icv_ratio","event","last_zero_days","first_positive_days","followup_days"]
    frame=pd.DataFrame(rows,columns=cols)
    intervals=frame[frame.event==1]
    widths=(intervals.first_positive_days-intervals.last_zero_days)
    bins=[0,365,730,1095,1825,float("inf")]
    hist=np.histogram(frame.followup_days.to_numpy(dtype=float),bins=bins)[0].tolist()
    report={"data_kind":"synthetic software fixture" if synthetic else "user-supplied research data; source authorization not verified by software",
            "input_participants":len(b),"included":len(frame),"excluded":excluded,
            "events":int(frame.event.sum()),"right_censored":int((frame.event==0).sum()),
            "median_event_interval_days":float(widths.median()) if len(widths) else None,
            "followup_bins_days":["0–364","365–729","730–1094","1095–1824","1825+"],"followup_counts":hist,
            "missing_predictors":{c:int(frame[c].isna().sum()) for c in ["age","mmse","hippocampus_icv_ratio"]},
            "status":"Input audit only; no survival model fitted and no new predictive performance estimated."}
    return frame,report

def run(baseline_path,visits_path,output,synthetic=False):
    if not synthetic: output=private_output(output)
    frame,report=prepare(pd.read_csv(baseline_path,dtype={"participant_id":str}),pd.read_csv(visits_path,dtype={"participant_id":str}),synthetic)
    report["input_sha256"]={"baseline":hashlib.sha256(Path(baseline_path).read_bytes()).hexdigest(),"visits":hashlib.sha256(Path(visits_path).read_bytes()).hexdigest()}
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    # All outputs for real data are local private material pending disclosure review.
    frame.to_csv(out/"cohort.csv",index=False)
    (out/"audit.json").write_text(json.dumps(report,indent=2,allow_nan=False))
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline",required=True);p.add_argument("--visits",required=True)
    p.add_argument("--output",default="private/longitudinal");p.add_argument("--synthetic",action="store_true")
    a=p.parse_args();run(a.baseline,a.visits,a.output,a.synthetic)
