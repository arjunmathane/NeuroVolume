import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {inferScenario, makeScenarioFile, readScenarioFile} from '../web/scenarios.mjs';
const bundle = {models:{}, model_sha256:{}};
for (const [study,file] of [['current','logistic.json'],['future','decline-logistic.json']]) {
  const bytes = fs.readFileSync(new URL('../models/'+file, import.meta.url));
  bundle.models[study] = JSON.parse(bytes); bundle.model_sha256[study] = crypto.createHash('sha256').update(bytes).digest('hex');
}
const profile = {Age:75, Sex:0, EDUC:16, SES:2, eTIV:1450, nWBV:.74, MMSE:28};
for (const [study,models] of Object.entries(bundle.models)) for (const [family,model] of Object.entries(models)) {
  test(study+'/'+family+' preserves inputs, missingness and exact replay', () => {
    const b = {...profile, [model.features.at(-1)]:null};
    const exported = makeScenarioFile(bundle, study, family, b, profile);
    const restored = readScenarioFile(JSON.stringify(exported), bundle);
    assert.deepEqual(restored, exported);
    assert.equal(restored.scenarios.b[model.features.at(-1)], null);
    assert.deepEqual(Object.keys(restored.scenarios.b), model.features);
    const before = inferScenario(model, b), after = inferScenario(model, restored.scenarios.b);
    assert.deepEqual(after,before);
    assert.equal(after.contributions.at(-1).imputed, true);
    assert.equal(after.contributions.at(-1).used,model.medians.at(-1));
    const difference = after.contributions.reduce((sum,row,i) => sum+row.contribution-inferScenario(model,profile).contributions[i].contribution,0);
    assert.ok(Math.abs(difference-(after.logOdds-inferScenario(model,profile).logOdds)) < 1e-12);
  });
}
test('pinning produces an independent snapshot; single-scenario exports have no invented reference', () => {
  const b = {...profile}; const file = makeScenarioFile(bundle,'current','mri',b,b); b.Age = 90;
  assert.equal(file.scenarios.a.Age,75); assert.equal(file.scenarios.b.Age,75);
  assert.equal(makeScenarioFile(bundle,'current','mri',profile).scenarios.a,null);
});
test('model identity and study are checked before restoring', () => {
  const file = makeScenarioFile(bundle,'current','mri',profile);
  for(const mutation of [f => f.model_sha256='0'.repeat(64), f=>f.study='future',f=>f.family='__proto__',f=>f.study='toString',f=>f.family=['mri']]) {
    const bad = structuredClone(file); mutation(bad);
    assert.throws(()=>readScenarioFile(JSON.stringify(bad),bundle));
  }
});
test('malformed, oversized, extra fields and invalid types are rejected', () => {
  const file = makeScenarioFile(bundle,'current','mri',profile,profile);
  for(const text of ['null','[]','{','x'.repeat(65537),'false']) assert.throws(()=>readScenarioFile(text,bundle));
  const mutations = [f=>f.schema_version=2,f=>f.patient_id='invented-for-rejection',f=>f.purpose='',
    f=>f.scenarios.b.Age='75',f=>f.scenarios.b.Age=true,f=>f.scenarios.b.Age=100,
    f=>f.scenarios.b.Sex=.5,f=>f.scenarios.b.SES=2.5,f=>f.scenarios.b.nWBV=74,
    f=>delete f.scenarios.b.eTIV,f=>f.scenarios.b=null];
  for(const mutation of mutations) {
    const bad = structuredClone(file); mutation(bad);
    assert.throws(()=>readScenarioFile(JSON.stringify(bad),bundle));
  }
  const proto = JSON.stringify(file).replace('"b":{','"b":{"__proto__":{},');
  assert.throws(()=>readScenarioFile(proto,bundle));
});
test('all-missing examples expose every substitution; non-finite and unknown fields fail', () => {
  const model = bundle.models.current.mri;
  const result = inferScenario(model, {});
  assert.ok(result.contributions.every((row,i)=>row.imputed && row.used===model.medians[i]));
  for(const value of [NaN,Infinity,-Infinity,'',true]) assert.throws(()=>inferScenario(model,{Age:value}));
  assert.throws(()=>inferScenario(model,{participant_id:1}));
});
