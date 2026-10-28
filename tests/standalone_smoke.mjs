// Execute the generated app's actual scripts against a minimal DOM adapter.
// This verifies behavior; it does not substitute for visual browser QA.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';

const html = fs.readFileSync('standalone/index.html', 'utf8');
assert(!/__\w+__/.test(html), 'Unresolved embedded artifact');
assert(!/<(?:script|link)[^>]+(?:src|href)=/i.test(html), 'Unexpected external dependency');
assert(!/\b(?:fetch|XMLHttpRequest|localStorage|sessionStorage|sendBeacon)\s*[.(]/.test(html), 'Unexpected transmission or persistent storage');
const elements = new Map(), downloads = [];
class Element {
  constructor() {this._value=''; this.textContent=''; this.innerHTML=''; this.listeners={}; this.children=[]; this.attributes={}; this.style={}; this.validity={badInput:false}; this.disabled=false; this.hidden=false;}
  set id(value) {this._id=value; elements.set(value,this);}
  get id() {return this._id;}
  set value(value) {this._value=String(value);}
  get value() {return this._value;}
  setAttribute(key,value) {this.attributes[key]=value;}
  addEventListener(type,fn) {this.listeners[type]=fn;}
  replaceChildren() {this.children=[];}
  append(...children) {this.children.push(...children);}
  click() {if(this.download) downloads.push({name:this.download,url:this.href});return this.listeners.click?.();}
}
for(const match of html.matchAll(/\bid="([^"]+)"/g)) {const el=new Element();el.id=match[1];}
for(const match of html.matchAll(/<input[^>]*id="([^"]+)"[^>]*value="([^"]+)"/g)) elements.get(match[1]).value=match[2];
elements.get('study').value='current';
const blobs = new Map();
const context=vm.createContext({document:{getElementById:id=>elements.get(id),createElement:()=>new Element()},
  console,Blob,URL:{createObjectURL:blob=>{const key='blob:'+blobs.size;blobs.set(key,blob);return key;},revokeObjectURL:()=>{}},setTimeout:()=>{}});
for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g))vm.runInContext(match[1],context);
const get=id=>elements.get(id);
const change=(id,value)=>{get(id).value=value;get(id).listeners.input?.();};
assert.equal(get('score').textContent,'0.228');
get('pinScenario').click();
assert.equal(get('scoreDifference').textContent,'0.000');
change('f_nWBV','.70');
assert.notEqual(get('candidateScore').textContent,get('referenceScore').textContent);
assert.equal(get('referenceScore').textContent,'0.228','Pinned reference must not change with B');
change('f_SES','');
assert.match(get('imputationSummary').textContent,/1 of 6/);
assert.ok(get('comparisonRows').children.some(row=>row.children.some(cell=>String(cell.textContent).includes('training median'))));
get('downloadScenario').click();
const download=downloads.at(-1);
assert.match(download.name,/current-mri-scenario.json/);
const scenario=JSON.parse(await blobs.get(download.url).text());
assert.equal(scenario.scenarios.b.SES,null);
assert.equal(scenario.scenarios.a.nWBV,.74);
assert.equal(scenario.model_sha256,crypto.createHash('sha256').update(fs.readFileSync('models/logistic.json')).digest('hex'));
change('f_Age','150');
assert.equal(get('score').textContent,'—');assert.equal(get('downloadScenario').disabled,true);
assert.match(get('imputationSummary').textContent,/No prediction or export is available/);
assert.equal(get('comparisonResults').hidden,true,'Invalid input must hide old comparison');
get('reset').click();
get('f_Age').validity.badInput=true;get('f_Age').value='';get('f_Age').listeners.input();
assert.equal(get('score').textContent,'—','An incomplete numeric edit must not become an imputed value');
get('reset').click();
// A successful restore applies both scenarios; a failed restore leaves prior state intact.
const restore=text=>get('restoreScenario').listeners.change({target:{files:[{size:text.length,text:async()=>text}],value:'fixture.json'}});
await restore(JSON.stringify(scenario));
assert.equal(get('score').textContent,get('candidateScore').textContent);
assert.equal(get('f_nWBV').value,'0.7');
assert.match(get('comparisonStatus').textContent,/restored/);
const previous=get('score').textContent;
await restore('{"participant_id":"rejection-fixture"}');
assert.equal(get('score').textContent,previous);assert.match(get('scenarioMessage').textContent,/Unsupported/);
get('family').value='cognition';get('family').listeners.change();
assert.equal(get('comparisonResults').hidden,true,'Different models must clear reference A');
get('study').value='future';get('study').listeners.change();
assert.match(get('finding').textContent,/43 participants/);
assert.equal(get('score').textContent,'0.175');
assert.ok(get('evidence').children.every(row=>row.children[2].textContent==='0.0%'));
const initial=get('survivalValues').textContent;
assert.match(initial,/synthetic event-free fraction/);
assert.equal((get('survivalChart').innerHTML.match(/<path /g)??[]).length,2);
assert.equal(get('survivalTable').children.length,3);
assert.match(get('survivalEvidence').textContent,/450 training participants; 150 held-out/);
change('sRatio','.003');assert.notEqual(get('survivalValues').textContent,initial);
change('sMmse','');assert.equal(get('survivalError').textContent,'');
change('sAge','150');assert.match(get('survivalError').textContent,/within/);
assert(!get('survivalChart').innerHTML.includes('<path '));assert.equal(get('survivalTable').children.length,0);
get('resetSurvival').click();assert.equal(get('survivalValues').textContent,initial);
get('downloadSurvival').click();get('downloadAudit').click();
assert.deepEqual(downloads.slice(-2).map(file=>file.name),['neurovolume-synthetic-survival-report.json','neurovolume-synthetic-audit.json']);
get('study').value='current';get('study').listeners.change();
assert.match(get('finding').textContent,/0.683 to 0.688/);
console.log('Standalone integration: scenario comparison/replay, invalid-import atomicity, input validation, model identity, missingness, evidence, survival tables, resets and exports passed.');
