import json
from pathlib import Path
import numpy as np
import pandas as pd
from neurovolume.decline import cohort, model
from neurovolume.core import export_logistic, predict_portable

def test_censoring_and_no_future_features(tmp_path):
    rows=[]
    def add(person, days, cdr):
        for i,(d,c) in enumerate(zip(days,cdr)):
            rows.append({"Subject ID":person,"Visit":i+1,"CDR":c,"MR Delay":d,
                         "M/F":"F","Age":70+i,"EDUC":16,"SES":2,"eTIV":1400,"nWBV":.75-i*.02,"MMSE":29-i})
    add("early",[0,700],[0,.5])
    add("observed",[0,1200],[0,0])
    add("short",[0,600],[0,0])
    add("uncertain",[0,800,1300],[0,0,.5])
    add("reverted",[0,1200,1500],[0,.5,0])
    add("already",[0,1200],[.5,1])
    p=tmp_path/"visits.csv";pd.DataFrame(rows).to_csv(p,index=False)
    x,counts=cohort(p)
    assert dict(zip(x["Subject ID"],x.target))=={"early":1,"observed":0}
    assert counts=={"eligible_baseline":5,"excluded_insufficient_followup":3}
    assert x.nWBV.eq(.75).all() and x.Age.eq(70).all()

def test_portable_decline_parity():
    x=pd.DataFrame({"Age":[65,70,75,80,85,90],"nWBV":[.8,.79,.76,.73,.7,.69]})
    fit=model().fit(x,[0,0,1,0,1,1]); exported=export_logistic(fit,list(x))
    for row,p in zip(x.to_dict("records"),fit.predict_proba(x)[:,1]):
        assert abs(predict_portable(exported,row)-p)<1e-12

def test_release_counts_and_models():
    root=Path(__file__).resolve().parents[1]
    r=json.loads((root/"reports/decline-results.json").read_text())
    c=r["cohort"]
    assert c["included"]+c["excluded_insufficient_followup"]==c["eligible_baseline"]
    assert c["events"]+c["non_events"]==c["included"]
    assert set(json.loads((root/"models/decline-logistic.json").read_text()))=={"age","age_mri"}
    for v in r["results"].values():
        assert len(v["per_repeat_metrics"])==10
        assert np.isclose(v["mean_repeated_oof_auc"],np.mean([m["auc"] for m in v["per_repeat_metrics"]]))
