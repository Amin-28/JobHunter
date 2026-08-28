/* JobMatch AI — web frontend. Stateless server; profile + saved live here. */
'use strict';

const S = {
  profile: null, keywords: [], rawJobs: [], offline: false, aiProvider: 'local',
  ok: [], selected: null,
  saved: JSON.parse(localStorage.getItem('jm_saved') || '[]'),
  query: { location: '', remote_only: false, salary_min: 0, salary_max: 10000000,
           posted_within: 'any', job_types: [], levels: [] },
  sort: 'Match score',
};
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

/* ---------- helpers ---------- */
async function api(path, body, isForm) {
  const opt = { method: 'POST' };
  if (isForm) opt.body = body;
  else { opt.headers = { 'Content-Type': 'application/json' }; opt.body = JSON.stringify(body); }
  const r = await fetch(path, opt);
  return r.json();
}
const TILE = ['#1B2027', '#3A4B6D', '#7A5230', '#5B6A5B', '#6B4B6B'];
function companyColor(n) { let h = 0; for (const c of n || '') h = (h * 31 + c.charCodeAt(0)) >>> 0; return TILE[h % 5]; }
function initials(n) { const p = (n || '?').replace(/-/g, ' ').split(/\s+/).filter(Boolean); return ((p[0]?.[0] || '?') + (p[1]?.[0] || '')).toUpperCase(); }
const SYM = { USD:'$', EUR:'€', GBP:'£', PKR:'₨', INR:'₹', JPY:'¥', AUD:'A$', CAD:'C$', NZD:'NZ$', SGD:'S$', AED:'AED ', SAR:'SAR ', ZAR:'R', NGN:'₦', BRL:'R$', MXN:'MX$', PLN:'zł ', CHF:'CHF ' };
function amt(n){ if(n>=1e6) return (n/1e6).toFixed(1).replace(/\.0$/,'')+'M'; if(n>=1000) return Math.floor(n/1000)+'k'; return ''+n; }
function salaryLabel(j){ if(j.salary_min==null||j.salary_max==null) return 'Salary not listed'; const s=SYM[j.currency]||j.currency+' '; return j.salary_min===j.salary_max? s+amt(j.salary_min): `${s}${amt(j.salary_min)} – ${s}${amt(j.salary_max)}`; }
function ringColor(sc){ if(sc>=75) return ['var(--accent)','var(--accent-ink)']; if(sc>=50) return ['var(--warn)','var(--warn-ink)']; return ['var(--text-dis)','var(--text-2)']; }
function ring(sc, d = 46, sw = 4.5, fs = 12) {
  const r = (d - sw) / 2 - 1, c = 2 * Math.PI * r, off = c * (1 - sc / 100), [col, tc] = ringColor(sc);
  return `<svg width="${d}" height="${d}" viewBox="0 0 ${d} ${d}"><circle cx="${d/2}" cy="${d/2}" r="${r}" fill="none" stroke="#E6EAEE" stroke-width="${sw}"/>
   <circle cx="${d/2}" cy="${d/2}" r="${r}" fill="none" stroke="${col}" stroke-width="${sw}" stroke-linecap="round"
   stroke-dasharray="${c}" stroke-dashoffset="${off}" transform="rotate(-90 ${d/2} ${d/2})"/>
   <text x="50%" y="50%" text-anchor="middle" dy=".35em" class="mono" font-size="${fs}" font-weight="600" fill="${tc}">${sc}</text></svg>`;
}
function logo(c, size = 40, fs = 14) { return `<div class="logo" style="background:${companyColor(c)};width:${size}px;height:${size}px;flex-basis:${size}px;font-size:${fs}px">${initials(c)}</div>`; }
function status(t) { $('#statusbar').textContent = t; }

/* ---------- location eligibility (mirrors filtering.py) ---------- */
const REGION = { pakistan:'asia', india:'asia', bangladesh:'asia', china:'asia', japan:'asia', singapore:'asia', malaysia:'asia', indonesia:'asia', philippines:'asia', vietnam:'asia', thailand:'asia',
  'united states':'na', usa:'na', canada:'na', mexico:'na', 'united kingdom':'eu', uk:'eu', germany:'eu', france:'eu', spain:'eu', italy:'eu', netherlands:'eu', poland:'eu', ireland:'eu',
  brazil:'latam', argentina:'latam', australia:'oceania', 'new zealand':'oceania', uae:'me', 'saudi arabia':'me', qatar:'me', israel:'me', nigeria:'africa', kenya:'africa', 'south africa':'africa', egypt:'africa' };
const SYN = { asia:['asia','apac','asia pacific','south asia'], africa:['africa','emea'], na:['north america','usa','us','canada','americas'], eu:['europe','emea','eu','uk'], latam:['latam','latin america','south america','americas'], oceania:['oceania','apac','australia','anz'], me:['middle east','emea','mena','gcc'] };
const UNI = ['worldwide','anywhere','global','remote','any','international'];
function locKeywords(loc){ if(!loc) return new Set(); const low=loc.toLowerCase(); const kw=new Set(UNI); const city=low.split(',')[0].split('·')[0].trim(); if(city) kw.add(city);
  for(const [c,reg] of Object.entries(REGION)) if(new RegExp(`\\b${c}\\b`).test(low)){ kw.add(c); (SYN[reg]||[reg]).forEach(x=>kw.add(x)); }
  for(const [reg,syns] of Object.entries(SYN)) if(low.includes(reg)) syns.forEach(x=>kw.add(x)); return kw; }
function locMatches(job, loc){ if(!loc.trim()) return true; const jl=(job.location||'').toLowerCase(); if(!jl) return true;
  const city=loc.toLowerCase().split(',')[0].trim(); if(city && jl.includes(city)) return true;
  for(const k of locKeywords(loc)) if(k && jl.includes(k)) return true; return false; }
const LVL = { junior:1, mid:2, senior:3, lead:4, staff:4, principal:5, intern:1 };
function jobLevel(t){ const low=(t||'').toLowerCase(); for(const [w,r] of Object.entries(LVL)) if(new RegExp(`\\b${w}\\b`).test(low)) return Math.min(r,4); return null; }
const POSTED = { '24h':1, '7d':7, '30d':30, any:1e4 };

function applyFilters() {
  const q = S.query;
  let jobs = S.rawJobs.filter(j => {
    if (q.remote_only && (j.mode||'').toLowerCase() !== 'remote') return false;
    if (!locMatches(j, q.location)) return false;
    if (q.job_types.length && !q.job_types.includes(j.type)) return false;
    if (q.levels.length) { const lv = jobLevel(j.title); const ranks = q.levels.map(l=>LVL[l.toLowerCase()]); if (lv!=null && !ranks.includes(lv)) return false; }
    if (j.currency === 'USD' && j.salary_min!=null && j.salary_max!=null) { if (j.salary_max < q.salary_min || j.salary_min > q.salary_max) return false; }
    if ((j.posted_days ?? 999) > (POSTED[q.posted_within] ?? 1e4)) return false;
    return true;
  });
  if (S.sort === 'Date posted') jobs.sort((a,b)=>(a.posted_days??999)-(b.posted_days??999));
  else if (S.sort === 'Salary') jobs.sort((a,b)=>(b.salary_max||0)-(a.salary_max||0));
  else jobs.sort((a,b)=>b.score-a.score);
  return jobs;
}

/* ---------- navigation ---------- */
function gates() { return { upload:true, profile:!!S.profile, search:!!S.profile, saved:S.saved.length>0 }; }
function nav(view) {
  const g = gates(); if (g[view] === false) return;
  $$('.view').forEach(v => v.classList.remove('active'));
  $('#' + view + '-view').classList.add('active');
  const idx = { upload:0, profile:1, search:2, saved:3 }[view];
  $$('.nav-row').forEach(r => {
    const v = r.dataset.nav, i = +r.dataset.i;
    r.classList.toggle('active', v === view);
    r.classList.toggle('disabled', g[v] === false);
    r.classList.toggle('done', g[v] && i < idx && v !== view);
  });
  if (view === 'profile') renderProfile();
  if (view === 'search') { if (!S.rawJobs.length) runSearch(); else renderResults(); }
  if (view === 'saved') renderSaved();
}
$$('.nav-row').forEach(r => r.addEventListener('click', () => nav(r.dataset.nav)));

/* ---------- theme ---------- */
function setTheme(t) {
  document.documentElement.dataset.theme = t; localStorage.setItem('jm_theme', t);
  $('#theme-icon').innerHTML = t === 'dark'
    ? '<circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3" stroke="currentColor" stroke-width="2"/>'
    : '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" fill="none" stroke="currentColor" stroke-width="2"/>';
}
$('#theme-btn').addEventListener('click', () => setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));
setTheme(localStorage.getItem('jm_theme') || 'light');

/* ---------- upload ---------- */
const drop = $('#drop');
$('#browse').addEventListener('click', () => $('#file').click());
$('#file').addEventListener('change', e => e.target.files[0] && uploadFile(e.target.files[0]));
['dragover'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add('over'); }));
['dragleave','drop'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove('over'); }));
drop.addEventListener('drop', e => { const f = e.dataTransfer.files[0]; if (f) uploadFile(f); });

async function uploadFile(file) {
  const ext = (file.name.split('.').pop() || '').toLowerCase();
  if (!['pdf','docx'].includes(ext)) return dropErr('Only PDF or DOCX files, please.');
  if (file.size > 10*1024*1024) return dropErr('That file is over 10 MB.');
  $('#drop-err').style.display = 'none';
  $('#drop-idle').style.display = 'none'; $('#drop-busy').style.display = 'block';
  $('#busy-title').textContent = 'Reading your resume…';
  let p = 15; $('#prog').style.width = '15%';
  const tick = setInterval(() => { p = Math.min(90, p + 8); $('#prog').style.width = p + '%'; }, 300);
  status('Parsing… · ' + file.name);
  const fd = new FormData(); fd.append('file', file);
  let res;
  try { res = await api('/api/parse', fd, true); } catch { res = { error: 'Upload failed.' }; }
  clearInterval(tick); $('#prog').style.width = '100%';
  if (res.error) { $('#drop-idle').style.display = 'block'; $('#drop-busy').style.display = 'none'; return dropErr(res.error); }
  S.profile = res.profile; S.keywords = res.keywords || []; S.aiProvider = res.ai || 'local';
  S.query.location = (S.profile.location || '').split(' · ')[0].trim();
  S.rawJobs = [];
  status('Profile ready · ' + (S.profile.skills?.length || 0) + ' skills' + (res.ai !== 'local' ? ' · ✨ ' + res.ai : ''));
  setTimeout(() => { $('#drop-idle').style.display = 'block'; $('#drop-busy').style.display = 'none'; nav('profile'); }, 400);
}
function dropErr(m) { const e = $('#drop-err'); e.textContent = m; e.style.display = 'block'; drop.classList.add('err'); setTimeout(()=>drop.classList.remove('err'), 3000); }

/* ---------- profile ---------- */
function renderProfile() {
  const p = S.profile; if (!p) return;
  const skills = (p.skills||[]).map(s => `<span class="chip ${s.confidence==='low'?'low':''}">${s.name}${s.confidence==='low'?' · low':''}</span>`).join('');
  const doms = (p.domains||[]).map(d => `<span class="chip">${d}</span>`).join('');
  $('#profile-body').innerHTML = `
    <h1 style="font-size:21px;font-weight:600">Here's what we read</h1>
    <p style="color:var(--text-3);font-size:12.5px;margin-top:4px">Fix anything that looks off — matching quality depends on it.</p>
    <div class="panel" style="padding:24px 26px;margin-top:20px;max-width:860px">
      <div style="display:flex;gap:14px;align-items:center">
        <div class="logo" style="background:var(--accent-bg);color:var(--accent);width:52px;height:52px;border-radius:6px;font-size:18px">${initials(p.name)}</div>
        <div><div style="font-size:19px;font-weight:600">${p.name||'—'}</div>
        <div style="color:var(--text-3);font-size:13px">${p.current_title||'—'} · ${(p.location||'').split(' · ')[0]}</div></div>
      </div>
      ${p.summary?`<p style="color:var(--text-2);font-size:12.5px;margin-top:14px">“${p.summary}”</p>`:''}
      ${doms?`<div class="tags" style="margin-top:11px">${doms}</div>`:''}
      <hr style="border:none;border-top:1px solid var(--rule);margin:22px 0">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px 34px">
        ${field('CURRENT TITLE', p.current_title)}
        ${field('TARGET TITLE', p.target_title)}
        ${field('YEARS OF EXPERIENCE', p.years + (p.years_span?`  <span style="color:var(--text-5);font-size:12px">(${p.years_span})</span>`:''))}
        ${field('LOCATION', p.location)}
      </div>
      <hr style="border:none;border-top:1px solid var(--rule);margin:22px 0">
      <div class="section-l">KEY SKILLS <span style="color:var(--text-dis);font-weight:400;margin-left:6px">${(p.skills||[]).length} detected</span></div>
      <div class="tags" style="margin-top:12px">${skills}</div>
    </div>
    <div style="display:flex;gap:14px;align-items:center;margin-top:22px">
      <button class="btn" onclick="nav('search')">Search Jobs</button>
      <span style="color:var(--text-4);font-size:12px">Searches every source using keywords from your profile.</span>
    </div>`;
}
function field(l, v) { return `<div><div class="section-l">${l}</div><div style="font-size:14px;margin-top:7px">${v||'—'}</div></div>`; }

/* ---------- search ---------- */
function renderFilters() {
  const q = S.query;
  $('#filters').innerHTML = `
    <div class="row-between" style="margin-bottom:14px"><b style="font-size:12.5px">Filters</b><a id="reset" style="font-size:11px;color:var(--text-4)">Reset</a></div>
    <div class="grp"><div class="section-l">LOCATION</div>
      <input type="text" id="f-loc" placeholder="City, country or region" value="${q.location}" style="margin-top:8px">
      <div class="row-between" style="margin-top:10px"><span style="font-size:12.5px;color:var(--text-2)">Remote only</span>
        <div class="toggle ${q.remote_only?'on':''}" id="f-remote"></div></div></div>
    <div class="grp"><div class="section-l">SALARY (USD, ANNUAL)</div>
      <div class="range" style="margin-top:12px"><input type="range" id="f-smin" min="0" max="250000" step="5000" value="${Math.min(q.salary_min,250000)}">
      <input type="range" id="f-smax" min="0" max="250000" step="5000" value="${q.salary_max>=1e7?250000:q.salary_max}"></div>
      <div class="row-between mono" style="font-size:11.5px;color:var(--text-2);margin-top:4px"><span id="smin-l">$0</span><span id="smax-l">$250k+</span></div></div>
    <div class="grp"><div class="section-l">DATE POSTED</div>
      <div class="seg" style="margin-top:10px">${['24h','7d','30d','any'].map(o=>`<button data-p="${o}" class="${q.posted_within===o?'on':''}">${o==='any'?'Any':o}</button>`).join('')}</div></div>
    <div class="grp"><div class="section-l">JOB TYPE</div>${['Full-time','Contract','Internship','Part-time'].map(t=>
      `<div class="checkrow ${q.job_types.includes(t)?'on':''}" data-type="${t}"><span class="box"></span>${t}</div>`).join('')}</div>
    <div class="grp" style="border:none"><div class="section-l">EXPERIENCE LEVEL</div>
      <div class="tags" style="margin-top:10px">${['Junior','Mid','Senior','Lead'].map(l=>`<span class="pill ${q.levels.includes(l)?'on':''}" data-lvl="${l}">${l}</span>`).join('')}</div></div>`;
  wireFilters();
}
function wireFilters() {
  const q = S.query, deb = debounce(() => renderResults(), 280);
  $('#f-loc').oninput = e => { q.location = e.target.value.trim(); deb(); };
  $('#f-remote').onclick = e => { q.remote_only = !q.remote_only; e.target.classList.toggle('on'); renderResults(); };
  const smin=$('#f-smin'), smax=$('#f-smax');
  const upSal=()=>{ let a=+smin.value,b=+smax.value; if(a>b)[a,b]=[b,a]; $('#smin-l').textContent='$'+(a/1000)+'k'; $('#smax-l').textContent=b>=250000?'$250k+':'$'+(b/1000)+'k'; q.salary_min=a; q.salary_max=b>=250000?1e7:b; };
  smin.oninput=upSal; smax.oninput=upSal; smin.onchange=renderResults; smax.onchange=renderResults;
  $$('#filters .seg button').forEach(b=>b.onclick=()=>{ $$('#filters .seg button').forEach(x=>x.classList.remove('on')); b.classList.add('on'); q.posted_within=b.dataset.p; renderResults(); });
  $$('#filters [data-type]').forEach(c=>c.onclick=()=>{ c.classList.toggle('on'); const t=c.dataset.type; q.job_types=c.classList.contains('on')?[...q.job_types,t]:q.job_types.filter(x=>x!==t); renderResults(); });
  $$('#filters [data-lvl]').forEach(p=>p.onclick=()=>{ p.classList.toggle('on'); const l=p.dataset.lvl; q.levels=p.classList.contains('on')?[...q.levels,l]:q.levels.filter(x=>x!==l); renderResults(); });
  $('#reset').onclick=()=>{ S.query={location:'',remote_only:false,salary_min:0,salary_max:1e7,posted_within:'any',job_types:[],levels:[]}; renderFilters(); renderResults(); };
}
function debounce(fn, ms){ let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a),ms); }; }

function renderTokens() {
  const tf = $('#tokenfield'); $$('.chip', tf).forEach(c=>c.remove());
  const inp = $('#kw-input');
  S.keywords.forEach(k => { const c=document.createElement('span'); c.className='chip'; c.innerHTML=`${k}<span class="x">✕</span>`;
    c.querySelector('.x').onclick=()=>{ S.keywords=S.keywords.filter(x=>x!==k); renderTokens(); runSearch(); };
    tf.insertBefore(c, inp); });
}
$('#kw-input').addEventListener('keydown', e => { if(e.key==='Enter'&&e.target.value.trim()){ S.keywords.push(e.target.value.trim()); e.target.value=''; renderTokens(); runSearch(); } });
$('#search-btn').addEventListener('click', runSearch);
$('#sort').addEventListener('change', e => { S.sort=e.target.value; renderResults(); });
$('#ai-btn').addEventListener('click', aiResearch);

async function runSearch() {
  renderFilters(); renderTokens();
  $('#count').textContent = 'Searching…';
  $('#results-list').innerHTML = Array(4).fill('<div class="jobcard"><div class="skel" style="width:40px;height:40px"></div><div class="jc-body"><div class="skel" style="width:180px;height:12px;margin-bottom:8px"></div><div class="skel" style="width:260px;height:10px"></div></div></div>').join('');
  status('Searching live sources…');
  const res = await api('/api/search', { profile: S.profile, keywords: S.keywords, location: S.query.location });
  S.rawJobs = res.jobs || []; S.ok = res.ok || []; S.offline = res.offline; S.aiProvider = res.ai;
  status(res.offline ? 'Offline — no sources responded'
    : `${S.rawJobs.length} jobs · ${(res.ok||[]).length} sources: ${(res.ok||[]).join(', ')}${res.ai!=='local'?' · ✨ '+res.ai:''}`);
  renderResults();
}
async function aiResearch() {
  $('#ai-btn').innerHTML = '<span class="spin"></span> Researching…'; $('#ai-btn').disabled = true;
  const res = await api('/api/keywords', { profile: S.profile });
  $('#ai-btn').innerHTML = '✨ AI research'; $('#ai-btn').disabled = false;
  if (res.keywords?.length) { S.keywords = res.keywords.slice(0,5); renderTokens(); runSearch();
    status(`Keywords from ${res.provider!=='local'?res.provider:'your résumé'}: ${S.keywords.join(', ')}`); }
}

function renderResults() {
  if ($('#f-loc')) {} else renderFilters();
  const jobs = applyFilters();
  const nf = activeFilters();
  $('#count').innerHTML = `<b>${nf&&S.rawJobs.length?`${jobs.length} of ${S.rawJobs.length}`:jobs.length} jobs</b>${nf?` · ${nf} filter${nf>1?'s':''} applied`:''}${S.offline?' · offline':''}`;
  const list = $('#results-list');
  if (!jobs.length) { list.innerHTML = `<div class="empty"><h3>${S.rawJobs.length?'No roles match these filters.':'No jobs found.'}</h3><p>${S.rawJobs.length?'Widen the location or clear filters.':'Try different keywords above.'}</p>${S.rawJobs.length?'<button class="btn sec" onclick="document.getElementById(\'reset\').click()" style="margin-top:14px">Clear filters</button>':''}</div>`; return; }
  list.innerHTML = jobs.map((j,i) => card(j,i)).join('');
  $$('.jobcard', list).forEach((el,i) => {
    el.style.animationDelay = Math.min(i,12)*32 + 'ms';
    el.onclick = ev => { if (ev.target.closest('.save-x')) return; openDetail(jobs[i]); };
    const sx = $('.save-x', el); if (sx) sx.onclick = () => { toggleSave(jobs[i]); renderResults(); };
  });
}
function activeFilters(){ const q=S.query; let n=0; if(q.location)n++; if(q.remote_only)n++; if(q.job_types.length)n++; if(q.levels.length)n++; if(q.posted_within!=='any')n++; if(q.salary_min>0||q.salary_max<1e7)n++; return n; }
function card(j,i) {
  const skills=(j.matched_skills||[]).slice(0,3).map(s=>`<span class="chip">${s}</span>`).join('');
  const extra=j.extra_skill_count?`<span class="chip muted">+${j.extra_skill_count}</span>`:'';
  const sc=j.salary_min!=null;
  return `<div class="jobcard ${isSaved(j)?'saved-mark':''}">
    ${logo(j.company)}
    <div class="jc-body"><div class="title-row"><span class="jc-title">${j.title}</span></div>
      <div class="jc-meta">${j.company} · ${j.location} (${j.mode}) · ${j.type} · <span style="color:var(--text-4)">${j.source}</span></div>
      <div class="tags"><span class="chip mono ${sc?'muted':'muted'}">${salaryLabel(j)}</span>${skills}${extra}
        <span class="save-x chip muted" style="cursor:pointer;margin-left:auto">${isSaved(j)?'★ Saved':'☆ Save'}</span></div></div>
    <div class="jc-right">${ring(j.score)}<span class="posted">${j.posted}</span></div></div>`;
}

/* ---------- detail ---------- */
async function openDetail(j) {
  S.selected = j; nav_raw('detail');
  const f = j.factors || {};
  const bars = [['Skills',f.skills],['Seniority',f.seniority],['Location',f.location],['Tooling',f.tooling]].map(([n,v])=>{
    v=v||['',0]; const col=v[1]<50?'var(--warn)':'var(--accent)';
    return `<div class="factor"><div class="row-between" style="font-size:11.5px"><span style="color:var(--text-2)">${n}</span><span class="mono" style="color:var(--text-2)">${v[0]}</span></div><div class="bar"><div style="width:${v[1]}%;background:${col}"></div></div></div>`;
  }).join('');
  const reqs=(j.requirements||[]).map(([met,t])=>`<div class="req"><span style="color:${met?'var(--accent)':'var(--danger)'}">${met?'✓':'✕'}</span><span style="color:${met?'var(--text-2)':'var(--text-4)'}">${t}${met?'':'  (not on your resume)'}</span></div>`).join('');
  const ap=j.apply||{type:'none',value:''}; const barCls=ap.type==='website'?'bar-web':ap.type==='email'?'bar-email':'bar-none';
  const apLabel={website:'APPLY ON COMPANY SITE',email:'APPLY BY EMAIL',form:'APPLICATION FORM',none:'NO APPLY LINK DETECTED'}[ap.type];
  const apBtn=ap.type==='none'?'':`<a class="btn" href="${ap.type==='email'?'mailto:'+ap.value:ap.value}" target="_blank">${ap.type==='email'?'Send Email':ap.type==='form'?'Open Form':'Visit Website'}</a>`;
  $('#detail-view').innerHTML = `<div class="dwrap">
    <div class="detail-main">
      <a onclick="nav('search')" style="font-size:12px;cursor:pointer">‹ Back to results</a>
      <div style="display:flex;gap:14px;align-items:flex-start;margin-top:14px">
        ${logo(j.company,46,16)}
        <div style="flex:1"><h2 style="font-size:21px;font-weight:600">${j.title}</h2>
          <div style="color:var(--text-3);font-size:13px;margin-top:4px">${j.company} · ${j.location} (${j.mode}) · ${j.type} · Posted ${j.posted}</div></div>
        <button class="btn sec save-toggle">${isSaved(j)?'★ Saved':'☆ Save Job'}</button>
      </div>
      <div class="apply-bar ${barCls}">
        <div style="flex:1"><div class="section-l" style="color:var(--accent-ink)">${apLabel}</div>
          <div class="mono" style="font-size:12.5px;color:var(--text-2);margin-top:4px">${ap.type==='none'?'Open the original listing to find how to apply.':ap.value}</div></div>${apBtn}</div>
      <h3 style="font-size:13.5px;font-weight:600;margin-top:6px">About the role</h3>
      <p style="color:var(--text-2);font-size:13px;line-height:1.65;margin-top:8px">${j.description||''}</p>
      <h3 style="font-size:13.5px;font-weight:600;margin-top:22px">Requirements</h3>${reqs}
      <h3 style="font-size:13.5px;font-weight:600;margin-top:22px">Benefits</h3>
      <p style="color:var(--text-2);font-size:12.5px;margin-top:8px">${j.benefits||''}</p>
    </div>
    <div class="detail-side">
      <div class="section-l">MATCH BREAKDOWN</div>
      <div style="display:flex;gap:12px;align-items:center;margin:12px 0">${ring(j.score,60,6,14)}
        <span style="color:var(--text-3);font-size:11.5px">Match against<br>your résumé</span></div>
      ${bars}
      <button class="btn ghost why-btn" style="width:100%;margin-top:6px;text-align:left">✨ Why this score?</button>
      <div class="why" id="why-panel" style="display:none"></div>
      <hr style="border:none;border-top:1px solid var(--border);margin:16px 0">
      <div class="section-l">SALARY</div>
      <div class="mono" style="font-size:15px;font-weight:600;margin-top:8px">${salaryLabel(j)}</div>
      <div style="color:var(--text-4);font-size:11.5px">${j.salary_min!=null?'Listed · '+j.currency:'Not listed by employer'}</div>
      <hr style="border:none;border-top:1px solid var(--border);margin:16px 0">
      <div class="section-l">SOURCE</div><div style="font-size:12.5px;margin-top:6px">${j.source}</div>
    </div></div>`;
  $('.save-toggle').onclick = e => { toggleSave(j); e.target.textContent = isSaved(j)?'★ Saved':'☆ Save Job'; };
  $('.why-btn').onclick = async () => {
    const panel=$('#why-panel'); panel.style.display='block'; $('.why-btn').style.display='none';
    panel.textContent='Thinking…'; const res=await api('/api/explain',{profile:S.profile, job:j});
    panel.textContent = res.text + (res.provider!=='local'?'\n\n✨ Explained by '+res.provider:'');
  };
}
function nav_raw(view){ $$('.view').forEach(v=>v.classList.remove('active')); $('#'+view+'-view').classList.add('active'); }

/* ---------- saved ---------- */
function isSaved(j){ return S.saved.some(s=>s.id===j.id); }
function toggleSave(j){ if(isSaved(j)) S.saved=S.saved.filter(s=>s.id!==j.id); else S.saved.unshift(j);
  localStorage.setItem('jm_saved', JSON.stringify(S.saved)); $('#saved-badge').textContent=S.saved.length;
  $('#saved-badge').classList.toggle('on',S.saved.length>0);
  $$('.nav-row[data-nav=saved]').forEach(r=>r.classList.toggle('disabled',!S.saved.length)); }
function renderSaved() {
  const b=$('#saved-body');
  if(!S.saved.length){ b.innerHTML='<div class="empty"><h3>Nothing saved yet.</h3><p>Bookmark a job from the results list.</p></div>'; return; }
  b.innerHTML = `<h1 style="font-size:21px;font-weight:600">Saved jobs</h1><p style="color:var(--text-3);font-size:12.5px;margin:4px 0 16px">${S.saved.length} saved</p>`
    + S.saved.map(j=>`<div class="saved-row">★ ${logo(j.company,34,12)}
      <div style="flex:1"><div style="font-weight:600;font-size:13.5px">${j.title}</div>
      <div style="color:var(--text-4);font-size:11.5px">${j.company} · ${j.location} · ${salaryLabel(j)}</div></div>
      <span class="mono" style="width:36px">${j.score}</span>
      <a class="btn sec open-d" data-id="${j.id}" style="padding:5px 11px;font-size:12px">Open</a>
      <a class="rm" data-id="${j.id}" style="cursor:pointer;color:var(--text-4)">Remove</a></div>`).join('');
  $$('.open-d').forEach(a=>a.onclick=()=>openDetail(S.saved.find(s=>s.id===a.dataset.id)));
  $$('.rm').forEach(a=>a.onclick=()=>{ toggleSave(S.saved.find(s=>s.id===a.dataset.id)); renderSaved(); });
}

/* ---------- settings modal ---------- */
const SET_SECTIONS = [
  ['AI · free', [['groq_key','Groq key','console.groq.com — free, fast'],['gemini_key','Google Gemini key','aistudio.google.com — free']]],
  ['Jobs', [['jooble_key','Jooble key','jooble.org/api/about — Pakistan jobs, free'],['rapidapi_key','RapidAPI key (JSearch)','LinkedIn/Indeed via Google — free tier']]],
  ['Advanced · optional', [['anthropic_api_key','Anthropic (Claude) key','paid'],['adzuna_app_id','Adzuna App ID','free'],['adzuna_app_key','Adzuna App Key','']]],
];
async function openSettings() {
  const st = await api2('/api/settings');
  const note = $('#settings-note');
  if (!st.local) { note.style.display='block'; note.textContent='This app is hosted, so keys are read-only here — set them as environment variables on the server. (Only the local machine can edit keys.)'; }
  else note.style.display='none';
  $('#settings-fields').innerHTML = SET_SECTIONS.map(([sec,rows]) => `<div class="set-sec">${sec}</div>` +
    rows.map(([k,label,hint])=>`<div class="set-field"><label>${label} ${hint?`<span>· ${hint}</span>`:''}</label>
      <input type="password" data-k="${k}" placeholder="${st.configured?.[k]?'•••••• saved — leave blank to keep':'paste key…'}" ${st.local?'':'disabled'}></div>`).join('')
  ).join('');
  $('#settings-save').style.display = st.local ? '' : 'none';
  $('#modal-bg').style.display = 'grid';
}
async function api2(path){ const r=await fetch(path); return r.json(); }
$('#settings-btn').addEventListener('click', openSettings);
$('#settings-cancel').addEventListener('click', ()=>$('#modal-bg').style.display='none');
$('#settings-test').addEventListener('click', async () => {
  const box = $('#test-results'); box.style.display='block';
  box.innerHTML = '<span class="spin"></span> Pinging every source (uses your saved keys)…';
  const loc = S.query.location || (S.profile?.location||'').split(' · ')[0] || 'Karachi, Pakistan';
  const res = await api('/api/test-sources', { location: loc });
  box.innerHTML = (res.results||[]).map(r => {
    if (r.status==='ok') return `<div style="color:var(--ok)">✓ <b>${r.name}</b> — ${r.count} jobs <span style="color:var(--text-4)">(${r.ms}ms)</span></div>`;
    if (r.status==='no_key') return `<div style="color:var(--text-4)">○ ${r.name} — no key configured</div>`;
    return `<div style="color:var(--danger)">✗ <b>${r.name}</b> — ${r.error}</div>`;
  }).join('') + `<div style="color:var(--text-4);margin-top:6px;font-size:11px">Location tested: ${loc}</div>`;
});
$('#modal-bg').addEventListener('click', e=>{ if(e.target.id==='modal-bg') $('#modal-bg').style.display='none'; });
$('#settings-save').addEventListener('click', async () => {
  const body = {};
  $$('#settings-fields input').forEach(i => { const v=i.value.trim(); if(v) body[i.dataset.k]=v; });
  const res = await api('/api/settings', body);
  $('#modal-bg').style.display='none';
  if (res.ok) { status(`Settings saved · ${(res.sources||[]).length} sources${res.ai!=='local'?' · ✨ '+res.ai:''}`);
    if (S.profile) { S.rawJobs=[]; if($('#search-view').classList.contains('active')) runSearch(); } }
  else status(res.error || 'Could not save settings');
});

/* ---------- boot ---------- */
$('#saved-badge').textContent = S.saved.length;
if (S.saved.length) $$('.nav-row[data-nav=saved]').forEach(r=>r.classList.remove('disabled'));
api('/api/status', {}).then(s => { if(s.ai && s.ai!=='local') status('Ready · AI: '+s.ai+' · '+(s.sources||[]).length+' sources'); }).catch(()=>{});
