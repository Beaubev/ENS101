const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('static/app.js', 'utf8');
// Execute the production renderer in a small DOM fixture; no student data or browser session.
const start = source.indexOf('function clearVmockReadiness(');
const end = source.indexOf('function assessmentDataFromReadiness(', start);
assert.ok(start >= 0 && end > start, 'VMock rendering functions exist');
class Element {
  constructor() { this.hidden = false; this.textContent = ''; this.className = ''; this.children = []; }
  replaceChildren() { this.children = []; this.textContent = ''; }
  append(...children) { this.children.push(...children); }
}
const ids = Object.fromEntries(['vmock-readiness','vmock-status','vmock-freshness','vmock-metrics','vmock-guidance'].map(id => [id, new Element()]));
const context = { $: selector => ids[selector.slice(1)], document: {createElement: () => new Element()}, formatReadinessTimestamp: value => value || '', Date };
vm.createContext(context);
vm.runInContext(source.slice(start, end), context);
const render = (record, status='fresh') => context.renderVmockReadiness({data:{vmock:record},sources:{vmock:{status,imported_at:'2026-10-01T10:20:00+00:00'}}});
const record = {signed_up:true,resume_uploaded:true,resume_upload_count:2,latest_score:0,latest_zone:'red',latest_subscores:{impact:0,presentation:0,competencies:0},first_score:20,highest_score:20,latest_upload_date:'2026-09-30'};
const text = () => ids['vmock-metrics'].children.map(row=>row.children.map(e=>e.textContent).join(' ')).join(' ');
render(record);
assert.match(ids['vmock-status'].textContent, /Red/);
assert.match(text(), /Latest score 0/);
assert.match(text(), /-20/);
assert.match(text(), /Impact 0/);
assert.ok(!text().includes('/ 100'), 'Unknown sub-score denominators must not be invented');
render(record,'stale');
assert.match(ids['vmock-freshness'].textContent, /older than 36 hours/);
assert.ok(!ids['vmock-metrics'].hidden, 'Last good metrics remain visible when stale');
render({...record,resume_uploaded:false,latest_zone:null,latest_score:null});
assert.match(ids['vmock-status'].textContent, /No resume/);
assert.ok(ids['vmock-metrics'].hidden);
render(null);
assert.match(ids['vmock-status'].textContent, /No VMock record/);
assert.equal(ids['vmock-metrics'].children.length, 0, 'Previous student metrics cleared');
render({...record,latest_zone:'blue'});
assert.ok(!ids['vmock-status'].className.includes('success'));
context.clearVmockReadiness();
assert.ok(ids['vmock-readiness'].hidden);
console.log('VMock renderer: scored, zero, decline, stale, no resume, missing, unknown, clear PASS');
