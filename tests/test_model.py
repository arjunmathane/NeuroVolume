import json
from pathlib import Path
import shutil
import subprocess
import joblib
import numpy as np
import pandas as pd
import pytest
from neurovolume.core import baseline, FEATURES, pipeline, metrics, predict_portable

ROOT = Path(__file__).resolve().parents[1]

def test_baseline_preserves_missing_values_and_ignores_future_labels(tmp_path):
    rows = [
        {'Subject ID':'a','Visit':2,'CDR':1,'M/F':'F','Age':72,'EDUC':16,'SES':2,'eTIV':1400,'nWBV':.7,'MMSE':23,'Group':'Converted'},
        {'Subject ID':'a','Visit':1,'CDR':0,'M/F':'F','Age':70,'EDUC':16,'SES':None,'eTIV':1420,'nWBV':.73,'MMSE':None,'Group':'Converted'},
        {'Subject ID':'b','Visit':1,'CDR':.5,'M/F':'M','Age':80,'EDUC':12,'SES':3,'eTIV':1600,'nWBV':.68,'MMSE':25,'Group':'Demented'},
    ]
    path=tmp_path/'synthetic.csv';pd.DataFrame(rows).to_csv(path,index=False)
    first,_=baseline(path)
    assert len(first)==2 and first.iloc[0].target==0
    assert pd.isna(first.iloc[0].SES) and pd.isna(first.iloc[0].MMSE)
    assert first.iloc[0].Age==70
    assert all(not set(f)&{'CDR','Group','Visit','Subject ID','MRI ID','ASF'} for f in FEATURES.values())

def test_duplicate_visits_rejected(tmp_path):
    row={'Subject ID':'a','Visit':1,'CDR':0,'M/F':'F','Age':70,'EDUC':16,'SES':2,'eTIV':1400,'nWBV':.7,'MMSE':28}
    path=tmp_path/'bad.csv';pd.DataFrame([row,row]).to_csv(path,index=False)
    with pytest.raises(ValueError,match='Duplicate'):baseline(path)

def test_imputation_is_learned_from_training_only():
    x=pd.DataFrame({'Age':[60,62,64,66,68,70]});y=[0,0,1,0,1,1]
    model=pipeline('logistic').fit(x,y)
    assert model['impute'].statistics_[0]==65
    model.predict_proba(pd.DataFrame({'Age':[None,96]}))
    assert model['impute'].statistics_[0]==65

def test_metric_definitions():
    m=metrics([0,0,1,1],[.1,.6,.7,.8])
    assert m['accuracy']==.75 and m['sensitivity']==1 and m['specificity']==.5
    assert m['confusion']=={'tn':1,'fp':1,'fn':0,'tp':2}

@pytest.mark.parametrize('family', FEATURES)
def test_portable_matches_sklearn_and_browser(family):
    """Compare independent Python, sklearn and TypeScript inference on synthetic inputs."""
    portable=json.loads((ROOT/'models/logistic.json').read_text())[family]
    fitted=joblib.load(ROOT/'models'/f'{family}_logistic.joblib')
    rng=np.random.default_rng(17)
    cases=[]
    for i in range(100):
        v={'Age':int(rng.integers(60,97)),'Sex':int(rng.integers(0,2)),
           'EDUC':int(rng.integers(6,24)),'SES':int(rng.integers(1,6)),
           'eTIV':float(rng.uniform(1100,2000)),'nWBV':float(rng.uniform(.64,.84)),
           'MMSE':int(rng.integers(4,31))}
        if i%3==0:v[portable['features'][i%len(portable['features'])]]=None
        cases.append(v)
    cases.append({f:None for f in portable['features']})
    x=pd.DataFrame(cases)[portable['features']].astype(float)
    expected=fitted.predict_proba(x)[:,1]
    actual=[predict_portable(portable,v) for v in cases]
    np.testing.assert_allclose(actual,expected,rtol=1e-12,atol=1e-12)
    if not shutil.which('node'):pytest.skip('Node required for browser parity test')
    script="import {infer} from " + json.dumps((ROOT/'demo/lib/inference.ts').as_uri()) + ";let input='';for await(const chunk of process.stdin)input+=chunk;const d=JSON.parse(input);console.log(JSON.stringify(d.cases.map(v=>infer(d.model,v).score)));"
    result=subprocess.run(['node','--experimental-strip-types','--input-type=module','-e',script],input=json.dumps({'model':portable,'cases':cases}),capture_output=True,text=True,check=True)
    np.testing.assert_allclose(json.loads(result.stdout),expected,rtol=1e-12,atol=1e-12)

@pytest.mark.parametrize('bad',[{'Age':59},{'Age':float('nan')},{'Sex':.5},{'Group':1},{'nWBV':73}])
def test_invalid_inference_rejected(bad):
    model=json.loads((ROOT/'models/logistic.json').read_text())['mri']
    with pytest.raises(ValueError):predict_portable(model,bad)

def test_report_and_demo_are_synchronized():
    assert json.loads((ROOT/'models/logistic.json').read_text())==json.loads((ROOT/'demo/lib/generated/models.json').read_text())
    report=json.loads((ROOT/'reports/results.json').read_text())
    assert report==json.loads((ROOT/'demo/lib/generated/results.json').read_text())
    assert len(report['results'])==12
    for r in report['results']:
        c=r['test']['confusion'];assert sum(c.values())==30
        assert r['test']['accuracy']==(c['tp']+c['tn'])/30
        assert r['auc_ci'][0]<=r['test']['auc']<=r['auc_ci'][1]

def test_local_split_and_predictions_when_available():
    path=ROOT/'private/splits.json'
    if not path.exists():pytest.skip('Private audit files intentionally excluded from distribution')
    split=json.loads(path.read_text());dev=set(split['development']);test=set(split['test'])
    assert len(dev)==120 and len(test)==30 and not dev&test
    for f in split['folds']:
        a,b=set(f['train']),set(f['validation'])
        assert not a&b and a|b==dev and not (a|b)&test
    predictions=pd.read_csv(ROOT/'private/test_predictions.csv')
    report=json.loads((ROOT/'reports/results.json').read_text())
    for r in report['results']:
        m=metrics(predictions.target,predictions[r['key']])
        assert m['confusion']==r['test']['confusion']
        assert m['auc']==pytest.approx(r['test']['auc'])
