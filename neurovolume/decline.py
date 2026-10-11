"""Exploratory three-year recorded-impairment pilot, not a clinical prognosis."""
import argparse, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from .core import baseline, metrics, export_logistic

HORIZON = 1095
FEATURES = {"age": ["Age"], "age_mri": ["Age", "nWBV"]}

def cohort(path, horizon=HORIZON):
    first, visits = baseline(path)
    if "MR Delay" not in visits or visits["MR Delay"].isna().any():
        raise ValueError("Complete MR Delay is required.")
    rows = []; excluded = 0
    for _, row in first[first.CDR == 0].iterrows():
        g = visits[visits["Subject ID"] == row["Subject ID"]].sort_values("Visit")
        t = g["MR Delay"] - g.iloc[0]["MR Delay"]
        if (t.diff().dropna() <= 0).any():
            raise ValueError("Follow-up times must strictly increase.")
        event_times = t[g.CDR > 0]
        event = float(event_times.min()) if len(event_times) else float("inf")
        # Only zero-CDR observations BEFORE first recorded impairment establish non-events.
        observed_zero = t[(g.CDR == 0) & (t < event)]
        if event <= horizon:
            target = 1
        elif len(observed_zero) and observed_zero.max() >= horizon:
            target = 0
        else:
            excluded += 1
            continue
        out = row.to_dict(); out["target"] = target
        rows.append(out)
    return pd.DataFrame(rows).reset_index(drop=True), {"eligible_baseline": int((first.CDR == 0).sum()), "excluded_insufficient_followup": excluded}

def model():
    return Pipeline([("impute", SimpleImputer(strategy="median")),
                     ("scale", StandardScaler()),
                     ("model", LogisticRegression(C=0.1, max_iter=2000, random_state=42))])

def run(data, output):
    out=Path(output); (out/"models").mkdir(parents=True,exist_ok=True); (out/"reports").mkdir(exist_ok=True)
    x, counts=cohort(data); y=x.target.to_numpy()
    if min(np.bincount(y, minlength=2)) < 3: raise ValueError("Need at least three participants in each class.")
    cv=list(RepeatedStratifiedKFold(n_splits=3,n_repeats=10,random_state=20260909).split(x,y))
    results={}; exported={}
    for family, columns in FEATURES.items():
        scores=np.zeros((10,len(x)))
        for i,(a,b) in enumerate(cv):
            fitted=model().fit(x.iloc[a][columns],y[a])
            scores[i//3,b]=fitted.predict_proba(x.iloc[b][columns])[:,1]
        per_repeat=[metrics(y,p) for p in scores]
        results[family]={"mean_repeated_oof_auc":float(np.mean([s["auc"] for s in per_repeat])),
                         "repeat_auc_range":[float(min(s["auc"] for s in per_repeat)),float(max(s["auc"] for s in per_repeat))],
                         "mean_repeated_oof_brier":float(np.mean([s["brier"] for s in per_repeat])),
                         "mean_repeated_oof_balanced_accuracy":float(np.mean([s["balanced_accuracy"] for s in per_repeat])),
                         "per_repeat_metrics":per_repeat}
        exported[family]=export_logistic(model().fit(x[columns],y), columns)
    report={"endpoint":"First recorded CDR > 0 within 1095 MRI-delay days after baseline CDR = 0",
            "status":"Exploratory internal-validation pilot; no independent test cohort or external validation",
            "horizon_days":HORIZON,"cohort":{**counts,"included":len(x),"events":int(y.sum()),"non_events":int((y==0).sum())},
            "source_sha256":hashlib.sha256(Path(data).read_bytes()).hexdigest(),
            "validation":"3-fold stratified CV repeated 10 times; same splits for both models; fold-local preprocessing; fixed C=0.1",
            "results":results,"model_use":"Full-cohort refits for illustrative inference only. CV metrics do not evaluate these final refits independently.",
            "limitations":["Eight events: unstable estimates; no clinical risk interpretation.","Horizon chosen after follow-up feasibility counts, before fitting prognostic models.","Repeat ranges describe split variability, not confidence intervals.","Excluded short follow-up may introduce selection bias.","CDR is aligned to MRI visits; scan intervals are only proxies for assessment intervals.","First recorded impairment is not biological onset or confirmed Alzheimer disease.","The parent study already explored this cohort; this is exploratory, not a new untouched test."]}
    (out/"reports/decline-results.json").write_text(json.dumps(report,indent=2))
    (out/"models/decline-logistic.json").write_text(json.dumps(exported,indent=2))
    print(json.dumps({"cohort":report["cohort"],"auc":{k:v["mean_repeated_oof_auc"] for k,v in results.items()}},indent=2))
    return report

if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--data",required=True); p.add_argument("--output",default=".")
    a=p.parse_args(); run(a.data,a.output)
