// CareFlow 30% milestone UI: login, new case (text), queue, case detail.
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pill = l => `<span class="pill ${esc(l)}">${esc(l || '?')}</span>`;
let token = sessionStorage.getItem('cf30_token');

async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = 'Bearer ' + token;
  const r = await fetch(path, { ...opts, headers, body: opts.json ? JSON.stringify(opts.json) : undefined });
  const d = await r.json();
  if (r.status === 401 && token) { sessionStorage.clear(); location.reload(); }
  if (!r.ok) throw new Error(d.detail || r.statusText);
  return d;
}

function nav() {
  $('nav').innerHTML = '<button data-v="queue">Queue</button><button data-v="new">New case</button>';
  $('nav').querySelectorAll('button').forEach(b => b.onclick = () => (b.dataset.v === 'queue' ? queue() : newCase()));
  $('who').innerHTML = '<button class="small" id="lo">Sign out</button>';
  $('lo').onclick = () => { sessionStorage.clear(); location.reload(); };
}

function login() {
  $('view').innerHTML = `<div class="panel" style="max-width:420px;margin:40px auto"><h2>Staff sign in</h2>
    <label>Username</label><input id="u" value="dr.mehta"><label>Password</label><input id="p" type="password" value="demo">
    <div class="row" style="margin-top:10px"><button class="primary" id="go">Sign in</button><span id="err" style="color:var(--bad)"></span></div></div>`;
  $('go').onclick = async () => {
    try { const r = await api('/api/auth/login', { method: 'POST', json: { username: $('u').value, password: $('p').value } });
      token = r.token; sessionStorage.setItem('cf30_token', token); nav(); queue(); } catch (e) { $('err').textContent = e.message; }
  };
}

async function queue() {
  const { cases } = await api('/api/queue');
  $('view').innerHTML = `<div class="panel"><h2>Review queue</h2><table><thead><tr><th>Priority</th><th>Case</th><th>Patient</th><th>Summary</th><th>Red flags</th></tr></thead>
    <tbody>${cases.map(c => `<tr class="clickable" data-c="${esc(c.code)}"><td>${pill(c.priority)}</td><td><b>${esc(c.code)}</b></td>
      <td>${esc(c.name || '-')} <span class="muted small">${esc(c.age ?? '?')} ${esc(c.sex || '')}</span></td><td class="small">${esc(c.summary)}</td>
      <td>${c.red_flags.map(r => `<span class="chip bad">${esc(r)}</span>`).join('')}</td></tr>`).join('')}</tbody></table></div>`;
  document.querySelectorAll('[data-c]').forEach(tr => tr.onclick = () => caseView(tr.dataset.c));
}

async function caseView(code) {
  const c = await api('/api/cases/' + code), a = c.analysis, p = a.priority;
  const seg = Object.fromEntries(a.segments.map(s => [s.id, s]));
  const hl = ev => { const t = seg[ev.segment_id]?.text || ''; return esc(t.slice(0, ev.start)) + '<mark>' + esc(t.slice(ev.start, ev.end)) + '</mark>' + esc(t.slice(ev.end)); };
  $('view').innerHTML = `<div class="panel"><button class="small" id="back">&larr; Queue</button>
    <h2>${esc(c.code)} &middot; ${esc(c.patient.name || '')} <span class="muted">(${esc(c.patient.age ?? '?')} ${esc(c.patient.sex || '')})</span></h2>
    <p>${pill(p.level)} <b>${esc(p.name)}</b> &middot; ${esc(p.explanation)}</p>
    ${a.not_processed.length ? `<p class="chip warn">Not processed in this milestone: ${esc(a.not_processed.join(', '))}</p>` : ''}</div>
    <div class="panel"><h3>Red flags</h3>${p.red_flags.map(r => `<div class="rf">${pill(r.priority)} <b>${esc(r.title)}</b> <span class="small muted">${esc(r.rule_id)}</span>
      ${r.evidence.map(e => `<div class="evidence-text small">${hl(e)}</div>`).join('')}</div>`).join('') || '<p class="muted">None matched.</p>'}</div>
    <div class="panel"><h3>Extracted findings</h3><table><thead><tr><th>Finding</th><th>Status</th><th>Duration (h)</th><th>Where it came from</th></tr></thead><tbody>
      ${Object.values(a.facts.symptoms).concat(Object.values(a.facts.history)).map(s => `<tr><td>${esc(s.label)}</td><td>${s.present ? 'reported' : 'denied'}</td>
        <td>${s.duration_hours ?? '-'}</td><td>${s.mentions.map(m => `<div class="small">${hl(m.evidence)}</div>`).join('')}</td></tr>`).join('')}</tbody></table>
      <h3 style="margin-top:12px">Timeline</h3>${a.timeline.map(t => `<div>${esc(t.label)}: ${t.onset ? 'since ' + esc(t.onset) : 'onset not stated'}</div>`).join('')}</div>`;
  $('back').onclick = queue;
}

function newCase() {
  $('view').innerHTML = `<div class="panel" style="max-width:760px"><h2>New case (text only)</h2>
    <div class="row"><div class="grow"><label>Name</label><input id="n"></div><div style="width:100px"><label>Age</label><input id="a" type="number"></div>
    <div style="width:100px"><label>Sex</label><select id="s"><option></option><option>F</option><option>M</option></select></div>
    <div style="width:140px"><label>Language</label><select id="l"><option value="en">English</option><option value="hi-en">Hinglish</option></select></div></div>
    <div class="row"><div style="width:120px"><label>SpO2 %</label><input id="v-spo2" type="number"></div><div style="width:120px"><label>HR</label><input id="v-hr" type="number"></div>
    <div style="width:120px"><label>SBP</label><input id="v-sbp" type="number"></div><div style="width:120px"><label>Temp C</label><input id="v-temp_c" type="number" step="0.1"></div></div>
    <label>Complaint</label><textarea id="t"></textarea><div class="row" style="margin-top:8px"><button class="primary" id="go">Create &amp; triage</button><span id="res"></span></div></div>`;
  $('go').onclick = async () => {
    const vitals = {}; ['spo2', 'hr', 'sbp', 'temp_c'].forEach(k => { const v = $('v-' + k).value; if (v !== '') vitals[k] = +v; });
    try { const r = await api('/api/cases', { method: 'POST', json: { name: $('n').value, age: $('a').value ? +$('a').value : null, sex: $('s').value, language: $('l').value, text: $('t').value, vitals } });
      caseView(r.code); } catch (e) { $('res').textContent = e.message; }
  };
}

if (token) { nav(); queue(); } else login();
