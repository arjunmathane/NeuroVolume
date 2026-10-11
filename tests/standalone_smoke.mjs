// Execute the generated app's actual scripts against a minimal DOM adapter.
// This verifies behavior; it does not substitute for visual browser QA.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const html = fs.readFileSync('standalone/index.html', 'utf8');
assert(!/__\w+__/.test(html), 'Unresolved embedded artifact');
assert(!/<(?:script|link)[^>]+(?:src|href)=/i.test(html), 'Unexpected external dependency');
class Element {
  constructor() {this.value = ''; this.textContent = ''; this.innerHTML = ''; this.listeners = {}; this.children = [];}
  addEventListener(type, fn) {this.listeners[type] = fn;}
  replaceChildren() {this.children = [];}
  append(...children) {this.children.push(...children);}
  click() {this.listeners.click?.();}
}
const elements = new Map([...html.matchAll(/\bid="([^"]+)"/g)].map(m => [m[1], new Element()]));
for (const match of html.matchAll(/<input[^>]*id="([^"]+)"[^>]*value="([^"]+)"/g)) elements.get(match[1]).value = match[2];
elements.get('study').value = 'current';
const context = vm.createContext({document: {getElementById: id => elements.get(id), createElement: () => new Element()},
  console, Blob, URL, setTimeout});
for (const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) vm.runInContext(match[1], context);
const get = id => elements.get(id);
const initial = get('survivalValues').textContent;
assert.match(initial, /synthetic event-free fraction/);
assert.equal((get('survivalChart').innerHTML.match(/<path /g) ?? []).length, 2);
assert.match(get('survivalEvidence').textContent, /450 training participants; 150 held-out/);
get('sRatio').value = '.003'; get('sRatio').listeners.input();
assert.notEqual(get('survivalValues').textContent, initial, 'Curve must change with MRI measurement');
get('sMmse').value = ''; get('sMmse').listeners.input();
assert.equal(get('survivalError').textContent, '');
get('sAge').value = '150'; get('sAge').listeners.input();
assert.match(get('survivalError').textContent, /within/);
assert(!get('survivalChart').innerHTML.includes('<path '), 'Invalid input must remove old curves');
get('resetSurvival').click();
assert.equal(get('survivalValues').textContent, initial);
get('study').value = 'future'; get('study').listeners.change();
assert.match(get('finding').textContent, /43 participants/);
assert.equal(get('score').textContent, '0.175');
get('downloadSurvival').click();
get('study').value = 'current'; get('study').listeners.change();
assert.match(get('finding').textContent, /0.683 to 0.688/);
console.log('Standalone source integration: rendering, model switching, curves, missingness, validation, reset and download handler passed.');
