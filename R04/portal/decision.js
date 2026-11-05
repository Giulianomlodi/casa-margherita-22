function openPlanDatabase(){
 return new Promise((resolve,reject)=>{const req=indexedDB.open('archai-local-plans',1);req.onupgradeneeded=()=>req.result.createObjectStore('plans');req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);});
}
async function planRequest(mode, action){
 const db=await openPlanDatabase();
 try{return await new Promise((resolve,reject)=>{const tx=db.transaction('plans',mode);const request=action(tx.objectStore('plans'));tx.oncomplete=()=>resolve(request.result);tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error);});}
 finally{db.close();}
}
function forgetPlan(id){planRequest('readwrite',s=>s.delete(id)).catch(()=>{});}
function planButtons(id){
 const group=document.createElement('div'),pick=document.createElement('input'),add=document.createElement('button'),open=document.createElement('button'),msg=document.createElement('span');
 group.className='local-plan';pick.type='file';pick.accept='application/pdf,image/jpeg,image/png,image/webp';pick.hidden=true;
 add.type=open.type='button';add.className=open.className='btn btn--line btn--small';add.textContent='Allega pianta';open.textContent='Apri pianta';open.hidden=true;msg.setAttribute('role','status');group.append(pick,add,open,msg);
 function refresh(){planRequest('readonly',s=>s.getKey(id)).then(k=>{open.hidden=!k;add.textContent=k?'Sostituisci pianta':'Allega pianta';}).catch(()=>{add.disabled=true;msg.textContent='Archivio locale non disponibile.'});}
 add.onclick=()=>pick.click();pick.onchange=async()=>{const f=pick.files[0];if(!f)return;if(!['application/pdf','image/jpeg','image/png','image/webp'].includes(f.type)||f.size>25*1024*1024){msg.textContent='Seleziona un PDF o una foto entro 25 MB.';return;}try{await planRequest('readwrite',s=>s.put(f,id));refresh();msg.textContent='Salvata nel browser.';}catch{msg.textContent='Spazio locale insufficiente.';}};
 open.onclick=async()=>{const win=window.open('about:blank','_blank');try{const f=await planRequest('readonly',s=>s.get(id));if(!f)throw Error();const url=URL.createObjectURL(f);if(win){win.opener=null;win.location.replace(url)}else{const a=document.createElement('a');a.href=url;a.download=f.name;a.click()}setTimeout(()=>URL.revokeObjectURL(url),120000);}catch{if(win)win.close();msg.textContent='Riapri la scheda e allega la pianta.';}};
 refresh();return group;
}

/* ARCHAI · Casa Margherita — decisione R04.
   Nessuna dipendenza. Ogni valore mostrato arriva da /decisioni/case.json,
   /decisioni/audit.json o da ciò che l'utente scrive in «Altre case»
   (salvato solo in localStorage, mai inviato). */
(() => {
  'use strict';

  const SRC = {
    cases: '/decisioni/case.json',
    audit: '/decisioni/audit.json',
    atlas: '/decisioni/atlante.html',
    overlay: '/decisioni/riscontro.svg'
  };
  const STORE_KEY = 'archai:casa-margherita:altre-case:v1';
  const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'L'];
  const CRITERIA = [
    ['status', 'Stato'],
    ['rooms', 'Camere'],
    ['garden', 'Giardino d’inverno'],
    ['high', 'Punto forte'],
    ['reason', 'Motivazione']
  ];
  const VERDICT = {
    ok: ['Coincide', 'chip--ok'],
    diff: ['Non coincide', 'chip--diff'],
    na: ['Dato mancante', 'chip--na']
  };
  const BASE_TITLE = document.title;
  const DASH = '—';

  const state = { house: null, options: [], recommended: null, selected: null };

  /* ---------- utilità ---------- */

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const str = v => (v == null ? '' : String(v).trim());
  const fmtNum = n => String(n).replace('.', ',');

  function h(tag, attrs, ...kids) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === 'class') node.className = v;
      else node.setAttribute(k, v === true ? '' : String(v));
    }
    for (const kid of kids.flat()) {
      if (kid == null || kid === false || kid === '') continue;
      node.append(kid instanceof Node ? kid : String(kid));
    }
    return node;
  }

  // Testo leggibile da un valore di JSON, senza inventare nulla.
  function show(v) {
    if (v == null) return '';
    if (Array.isArray(v)) return v.map(show).filter(Boolean).join(', ');
    if (typeof v === 'number') return Number.isFinite(v) ? fmtNum(v) : '';
    if (typeof v === 'boolean') return v ? 'Sì' : 'No';
    if (typeof v === 'object') return '';
    return str(v);
  }

  // Numero "puro" (eventualmente con unità): usato solo per confronti e proporzioni.
  function strictNum(v) {
    if (typeof v === 'number') return Number.isFinite(v) ? { n: v, u: '' } : null;
    const m = str(v).match(/^(-?\d+(?:[.,]\d+)?)\s*([^\d\s][^\d]*)?$/);
    if (!m) return null;
    const u = str(m[2]).toLowerCase().replace('²', '2').replace(/^mq$/, 'm2');
    return { n: Number(m[1].replace(',', '.')), u };
  }

  function looseNum(v) {
    if (typeof v === 'number') return Number.isFinite(v) ? v : null;
    const m = str(v).match(/-?\d+(?:[.,]\d+)?/);
    return m ? Number(m[0].replace(',', '.')) : null;
  }

  function areaText(v) {
    const p = strictNum(v);
    return p && !p.u ? `${fmtNum(p.n)} m²` : show(v);
  }

  function safeUrl(v) {
    const s = str(v);
    if (!s) return null;
    try {
      const u = new URL(s, location.href);
      return ['http:', 'https:', location.protocol].includes(u.protocol) ? u.href : null;
    } catch {
      return null;
    }
  }

  const slug = v => str(v).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

  const uid = () => (window.crypto && typeof crypto.randomUUID === 'function')
    ? crypto.randomUUID()
    : `c${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;

  function say(msg) {
    const el = $('[data-announce]');
    if (!el) return;
    el.textContent = '';
    setTimeout(() => { el.textContent = msg; }, 60);
  }

  // Salto immediato in cima, anche con scroll-behavior: smooth.
  function jumpTop() {
    const root = document.documentElement;
    const prev = root.style.scrollBehavior;
    root.style.scrollBehavior = 'auto';
    window.scrollTo(0, 0);
    root.style.scrollBehavior = prev;
  }

  function focusQuiet(el) {
    if (!el) return;
    if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1');
    el.focus({ preventScroll: true });
  }

  function setState(name, message, { error = false, href = null } = {}) {
    const el = $(`[data-state="${name}"]`);
    if (!el) return;
    el.hidden = false;
    el.classList.toggle('is-error', error);
    el.replaceChildren(message);
    if (href) el.append(' ', h('a', { href }, 'Apri il file'));
  }

  function clearState(name) {
    const el = $(`[data-state="${name}"]`);
    if (el) el.hidden = true;
  }

  function why(err) {
    if (err instanceof SyntaxError) return 'formato non valido';
    const m = str(err && err.message);
    return /^HTTP \d+/.test(m) ? m : 'file non raggiungibile';
  }

  async function getJSON(url) {
    const res = await fetch(url, { cache: 'no-cache', headers: { Accept: 'application/json' } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  /* ---------- proposte A/B/C ---------- */

  function letterOf(opt) {
    const m = str(opt && opt.id).toUpperCase().match(/(?:^|[^A-Z])([ABCDEFL])$/);
    return m ? m[1] : null;
  }

  function pickHouse(data) {
    const houses = Array.isArray(data && data.houses)
      ? data.houses.filter(x => x && typeof x === 'object')
      : [];
    return houses.find(x => /margherita/i.test(`${str(x.id)} ${str(x.name)}`)) || houses[0] || null;
  }

  function activeOptions(house) {
    const list = Array.isArray(house && house.options)
      ? house.options.filter(o => o && typeof o === 'object')
      : [];
    const found = new Map();
    for (const o of list) {
      const l = letterOf(o);
      if (l && !found.has(l)) found.set(l, o);
    }
    if (!found.size) list.slice(0, LETTERS.length).forEach((o, i) => found.set(LETTERS[i], o));
    return LETTERS.filter(l => found.has(l)).map(l => ({ ...found.get(l), letter: l }));
  }

  function findRecommended(opts) {
    const by = (key, re) => opts.find(o => re.test(str(o[key])));
    const hit = by('title', /casa con guardaroba/i)
      || by('status', /^\s*(proposta\s+)?(consigliat|raccomandat)/i)
      || by('title', /guardaroba/i);
    return hit ? hit.letter : null;
  }

  function variantFromUrl() {
    const v = str(new URLSearchParams(location.search).get('variante')).toUpperCase();
    return state.options.some(o => o.letter === v) ? v : null;
  }

  function variantHref(letter) {
    const u = new URL(location.href);
    u.searchParams.set('variante', letter);
    u.hash = 'confronto';
    return `${u.pathname}${u.search}${u.hash}`;
  }

  const optionLink = o => safeUrl(o.link) || `${SRC.atlas}?variante=${encodeURIComponent(o.letter)}`;
  const optionTitle = o => show(o.title) || `Proposta ${o.letter}`;

  function renderCases(data) {
    const house = pickHouse(data);
    state.house = house;
    state.options = activeOptions(house);
    if (!state.options.length) {
      setState('confronto', 'case.json non contiene proposte per questa casa. Nessuna proposta viene mostrata al suo posto.', { href: SRC.cases });
      return false;
    }
    state.recommended = findRecommended(state.options);
    if (house && show(house.place)) $('[data-place]').textContent = ` · ${show(house.place)}`;

    buildCards();
    buildTable();
    clearState('confronto');
    select(variantFromUrl() || state.recommended || state.options[0].letter, { announce: false });
    return true;
  }

  function buildCards() {
    const list = $('[data-cards]');
    list.replaceChildren(...state.options.map(o => {
      const rec = o.letter === state.recommended;
      const photo = safeUrl(o.photo);
      const img = photo ? h('img', { src: photo, alt: '', loading: 'lazy', decoding: 'async' }) : null;
      if (img) img.addEventListener('error', () => img.parentElement.classList.add('is-missing'));

      return h('li', { class: rec ? 'card is-recommended' : 'card', 'data-letter': o.letter },
        h('div', { class: 'card__photo' },
          img || h('span', { class: 'card__nophoto' }, 'Nessuna immagine nel file')),
        h('div', { class: 'card__body' },
          h('div', { class: 'card__meta' },
            h('span', { class: 'card__letter', 'aria-hidden': 'true' }, o.letter),
            rec ? h('span', { class: 'card__badge' }, 'Consigliata') : null),
          h('h3', { class: 'card__title' },
            h('a', { class: 'card__select', href: variantHref(o.letter), 'data-variant': o.letter },
              h('span', { class: 'sr-only' }, `Proposta ${o.letter}${rec ? ', consigliata' : ''}: `),
              optionTitle(o))),
          show(o.status) ? h('p', { class: 'card__status' }, show(o.status)) : null,
          show(o.summary) ? h('p', { class: 'card__summary' }, show(o.summary)) : null,
          h('p', { class: 'card__foot' },
            h('span', { class: 'card__state', 'aria-hidden': 'true' }, 'Seleziona'),
            h('a', { class: 'card__atlas', href: optionLink(o) },
              'Modello nell’atlante',
              h('span', { class: 'sr-only' }, `, proposta ${o.letter}`)))));
    }));
    list.hidden = false;
  }

  function buildTable() {
    const table = $('[data-compare]');
    const head = h('tr', null,
      h('th', { scope: 'col', class: 'compare__corner' }, h('span', { class: 'sr-only' }, 'Criterio')),
      state.options.map(o => h('th', { scope: 'col', 'data-letter': o.letter },
        h('a', { href: variantHref(o.letter), 'data-variant': o.letter },
          h('span', { class: 'compare__letter' }, o.letter),
          h('span', { class: 'compare__name' }, optionTitle(o))),
        o.letter === state.recommended ? h('span', { class: 'compare__rec' }, 'Consigliata') : null)));

    const rows = CRITERIA.map(([key, label]) => h('tr', null,
      h('th', { scope: 'row' }, label),
      state.options.map(o => {
        const v = show(o[key]);
        return h('td', { 'data-letter': o.letter, class: v ? null : 'is-empty' }, v || 'Non indicato');
      })));

    rows.push(h('tr', null,
      h('th', { scope: 'row' }, 'Modello'),
      state.options.map(o => h('td', { 'data-letter': o.letter },
        h('a', { href: optionLink(o) }, `Apri ${o.letter} nell’atlante`)))));

    table.tHead.replaceChildren(head);
    table.tBodies[0].replaceChildren(...rows);
    $('[data-compare-wrap]').hidden = false;
  }

  function select(letter, { push = false, announce = true } = {}) {
    const opt = state.options.find(o => o.letter === letter) || state.options[0];
    if (!opt) return;
    state.selected = opt.letter;

    $$('[data-cards] .card').forEach(card => {
      const on = card.dataset.letter === opt.letter;
      card.classList.toggle('is-selected', on);
      $('.card__state', card).textContent = on ? 'Selezionata' : 'Seleziona';
    });
    $$('a[data-variant]').forEach(a => {
      if (a.dataset.variant === opt.letter) a.setAttribute('aria-current', 'true');
      else a.removeAttribute('aria-current');
    });
    $$('[data-compare] [data-letter]').forEach(cell => {
      cell.classList.toggle('is-selected', cell.dataset.letter === opt.letter);
    });

    renderDetail(opt);
    if (push && variantFromUrl() !== opt.letter) {
      history.pushState({ variante: opt.letter }, '', variantHref(opt.letter));
    }
    if (announce) say(`Proposta ${opt.letter} selezionata: ${optionTitle(opt)}.`);
  }

  function fill(sel, value, wrapSel) {
    const el = $(sel);
    el.textContent = value;
    (wrapSel ? $(wrapSel) : el).hidden = !value;
  }

  function renderDetail(o) {
    const rec = o.letter === state.recommended;
    $('[data-detail-eyebrow]').textContent = `Proposta ${o.letter}${rec ? ' · consigliata' : ''}`;
    $('[data-detail-title]').textContent = optionTitle(o);
    fill('[data-detail-status]', show(o.status));
    fill('[data-detail-summary]', show(o.summary));
    fill('[data-detail-reason]', show(o.reason), '.detail__why');

    const link = $('[data-detail-link]');
    link.href = optionLink(o);
    link.textContent = `Apri il modello ${o.letter} nell’atlante`;

    const img = $('[data-detail-photo]');
    const none = $('[data-detail-nophoto]');
    const src = safeUrl(o.photo);
    $('[data-overlay]').hidden=true; $('[data-overlay-toggle]').textContent='Guarda la pianta'; $('[data-overlay-toggle]').setAttribute('aria-pressed','false'); img.hidden=false;
    img.alt = `Proposta ${o.letter}, ${optionTitle(o)}`;
    if (!src) {
      img.hidden = true;
      img.removeAttribute('src');
      none.textContent = 'case.json non indica un’immagine per questa proposta.';
      none.hidden = false;
    } else if (img.getAttribute('src') !== src) {
      none.hidden = true;
      img.hidden = false;
      img.src = src;
    }
    $('[data-detail]').hidden = false;
  }

  function initDetailPhoto() {
    const img = $('[data-detail-photo]');
    const none = $('[data-detail-nophoto]');
    img.addEventListener('error', () => {
      if (!img.getAttribute('src')) return;
      img.hidden = true;
      none.textContent = 'L’immagine di questa proposta non è raggiungibile.';
      none.hidden = false;
    });
  }

  function failCases(err) {
    setState('confronto',
      `Non è stato possibile leggere case.json (${why(err)}). Le proposte non vengono mostrate e nessun dato le sostituisce.`,
      { error: true, href: SRC.cases });
  }

  function onVariantClick(e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = e.target.closest('a[data-variant]');
    if (!a || !state.options.some(o => o.letter === a.dataset.variant)) return;
    e.preventDefault();
    select(a.dataset.variant, { push: true });
    if (a.hasAttribute('data-jump')) {
      $('#confronto').scrollIntoView();
      const card = $('[data-cards] .card.is-selected .card__select');
      if (card) card.focus({ preventScroll: true });
    }
  }

  function onPopState() {
    route();
    if (state.options.length) {
      select(variantFromUrl() || state.recommended || state.options[0].letter, { announce: false });
    }
  }

  /* ---------- riscontro sovrapposto ---------- */

  function initOverlay() {
    const btn=$('[data-overlay-toggle]'), layer=$('[data-overlay]'), img=$('[data-detail-photo]');
    btn.addEventListener('click',()=>{
      const on=btn.getAttribute('aria-pressed')!=='true';
      btn.setAttribute('aria-pressed',String(on)); btn.textContent=on?'Guarda il render':'Guarda la pianta';
      const opt=state.options.find(o=>o.link===new URL($('[data-detail-link]').href).pathname+new URL($('[data-detail-link]').href).search);
      const id=opt?.letter||new URL($('[data-detail-link]').href).searchParams.get('variante')||'A';
      layer.src=['F','L'].includes(id)?'/due-camere/'+id+'-L1.svg':'/decisioni/'+id+'-pianta.svg';layer.hidden=!on;img.hidden=on;
      $('[data-overlay-msg]').textContent=on?'Pianta arredata ricavata dalla stessa geometria del modello.':'Vista calcolata in Blender.';
    });
  }
  /* ---------- audit: aree, documento e disegno, rilievi ---------- */

  function renderAudit(audit) {
    const arr = key => (audit && Array.isArray(audit[key]) ? audit[key] : []);
    renderRooms(arr('rooms').filter(r => r && typeof r === 'object'));
    renderUnits(arr('units').filter(u => u && typeof u === 'object'));
    renderFindings(arr('findings').map(show).filter(Boolean));
  }

  function renderRooms(rooms) {
    if (!rooms.length) return setState('aree', 'audit.json non elenca vani.');
    const values = rooms.map(r => looseNum(r.area));
    const max = Math.max(0, ...values.filter(n => n > 0));

    const rows = rooms.map((r, i) => {
      const n = values[i];
      const area = areaText(r.area);
      return h('tr', { id: str(r.id) ? `vano-${slug(r.id)}` : null },
        h('th', { scope: 'row' }, show(r.name) || show(r.id) || 'Vano senza nome'),
        h('td', { class: 'num', 'data-label': 'Superficie' },
          area ? h('span', null, area) : h('span', { class: 'muted' }, 'Non indicata'),
          n > 0 && max > 0
            ? h('span', { class: 'bar', 'aria-hidden': 'true' }, h('i', { style: `width:${(n / max * 100).toFixed(1)}%` }))
            : null),
        h('td', { 'data-label': 'Luce' }, show(r.span) || DASH),
        h('td', { class: 'note', 'data-label': 'Note' }, show(r.note) || DASH));
    });

    $('[data-rooms] tbody').replaceChildren(...rows);
    clearState('aree');
    $('[data-rooms-wrap]').hidden = false;
  }

  function verdict(doc, draw) {
    const a = show(doc);
    const b = show(draw);
    if (!a || !b) return 'na';
    const x = strictNum(doc);
    const y = strictNum(draw);
    if (x && y) return Math.abs(x.n - y.n) < 1e-9 && (!x.u || !y.u || x.u === y.u) ? 'ok' : 'diff';
    const norm = s => s.toLowerCase().replace(/\s+/g, ' ');
    return norm(a) === norm(b) ? 'ok' : 'diff';
  }

  function tallyText(total, ok, diff, na) {
    const p = (n, one, many) => `${n} ${n === 1 ? one : many}`;
    const parts = [p(ok, 'coincide', 'coincidono')];
    if (diff) parts.push(p(diff, 'non coincide', 'non coincidono'));
    if (na) parts.push(p(na, 'ha un dato mancante', 'hanno un dato mancante'));
    return `${p(total, 'voce confrontata', 'voci confrontate')}: ${parts.join(', ')}.`;
  }

  function renderUnits(units) {
    if (!units.length) return setState('unita', 'audit.json non elenca voci da confrontare.');
    const count = { ok: 0, diff: 0, na: 0 };

    const rows = units.map(u => {
      const v = u.label.includes('Scarto') ? 'diff' : /Interni|Camere, cucina|^Bagno$|Ingresso/.test(u.label) ? 'ok' : 'na';
      count[v] += 1;
      const cls=VERDICT[v][1];const label={ok:'Compatibile sulla carta',diff:'Da riconciliare',na:'Criteri distinti'}[v];
      return h('tr', { class: `is-${v}` },
        h('th', { scope: 'row' }, show(u.label) || 'Voce senza nome'),
        h('td', { class: 'num', 'data-label': 'Documento' }, show(u.doc) || DASH),
        h('td', { class: 'num', 'data-label': 'Disegno' }, show(u.draw) || DASH),
        h('td', { 'data-label': 'Esito' }, h('span', { class: `chip ${cls}` }, label)),
        h('td', { class: 'note', 'data-label': 'Note' }, show(u.note) || DASH));
    });

    $('[data-units] tbody').replaceChildren(...rows);
    const tally = $('[data-units-tally]');
    tally.textContent='Confronto per omogeneità di superficie. Per il garage la carta restituisce circa 51 m² contro 52 m² dichiarati.';
    tally.hidden = false;
    clearState('unita');
    $('[data-units-wrap]').hidden = false;
  }

  function renderFindings(list) {
    if (!list.length) return setState('rilievi', 'audit.json non riporta rilievi.');
    const ol = $('[data-findings]');
    ol.replaceChildren(...list.map(t => h('li', null, t)));
    clearState('rilievi');
    ol.hidden = false;
  }

  function failAudit(err) {
    const msg = `Non è stato possibile leggere audit.json (${why(err)}). Nessun valore sostitutivo viene mostrato.`;
    ['aree', 'unita', 'rilievi'].forEach(name => setState(name, msg, { error: true, href: SRC.audit }));
  }

  /* ---------- hero ---------- */

  function initHero() {
    const img = $('[data-hero-img]');
    const fail = () => {
      img.hidden = true;
      $('[data-hero-missing]').hidden = false;
    };
    img.addEventListener('error', fail);
    if (img.complete && !img.naturalWidth) fail();
  }

  function heroStatus(casesOk, auditOk) {
    const el = $('[data-hero-status]');
    if (!casesOk || !auditOk) {
      el.classList.add('is-warn');
      el.textContent = 'Uno o più file di verifica non sono raggiungibili: le sezioni interessate restano vuote, senza dati sostitutivi.';
      return;
    }
    const rec = state.options.find(o => o.letter === state.recommended);
    el.replaceChildren(
      rec ? 'Nel confronto è la ' : '',
      rec ? h('a', { href: variantHref(rec.letter), 'data-variant': rec.letter, 'data-jump': '' }, `proposta ${rec.letter}`) : null,
      rec ? '. ' : '',
      'Rilievo metrico e verifica del terrazzo ancora da acquisire.');
  }

  /* ---------- viste ---------- */

  let view = null;

  function route() {
    let id = '';
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { id = ''; }
    const next = id === 'altre-case' ? 'altre' : 'casa';
    if (next === view) return;
    const initial = view === null;
    view = next;

    $$('[data-view]').forEach(v => { v.hidden = v.dataset.view !== next; });
    const nav = $('[data-nav-altre]');
    if (next === 'altre') nav.setAttribute('aria-current', 'page');
    else nav.removeAttribute('aria-current');
    document.title = next === 'altre' ? `Altre case · ${BASE_TITLE}` : BASE_TITLE;
    if (initial) return;

    if (next === 'altre') {
      jumpTop();
      $('#altre-titolo').focus({ preventScroll: true });
      return;
    }
    const target = id ? document.getElementById(id) : null;
    if (target) {
      target.scrollIntoView();
      focusQuiet(target);
    } else {
      jumpTop();
      focusQuiet($('#titolo'));
    }
  }

  /* ---------- Altre case (solo localStorage) ---------- */

  const Altre = (() => {
    let list = [];
    let editing = null;
    let persistent = false;
    let ui = null;

    function canStore() {
      try {
        const k = `${STORE_KEY}:prova`;
        localStorage.setItem(k, '1');
        localStorage.removeItem(k);
        return true;
      } catch {
        return false;
      }
    }

    function clean(r) {
      if (!r || typeof r !== 'object' || !str(r.name)) return null;
      const created = Number(r.created) || Date.now();
      return {
        id: str(r.id) || uid(),
        name: str(r.name).slice(0, 80),
        place: str(r.place).slice(0, 80),
        area: typeof r.area === 'number' && Number.isFinite(r.area) && r.area > 0 ? r.area : null,
        rooms: typeof r.rooms === 'number' && Number.isInteger(r.rooms) && r.rooms >= 0 ? r.rooms : null,
        garage: r.garage === 'si' || r.garage === 'no' ? r.garage : '',
        notes: str(r.notes).slice(0, 600),
        created,
        updated: Number(r.updated) || created
      };
    }

    function read() {
      if (!persistent) return list;
      try {
        const data = JSON.parse(localStorage.getItem(STORE_KEY) || '[]');
        return Array.isArray(data) ? data.map(clean).filter(Boolean) : [];
      } catch {
        return [];
      }
    }

    function write() {
      if (!persistent) return false;
      try {
        localStorage.setItem(STORE_KEY, JSON.stringify(list));
        return true;
      } catch {
        return false;
      }
    }

    // Cifre con virgola o punto decimale, punto delle migliaia facoltativo; il resto è rifiutato.
    function parseArea(raw) {
      let s = raw.replace(/\s+/g, '').replace(/(m²|m2|mq)$/i, '');
      if (/^\d{1,3}(\.\d{3})+(,\d+)?$/.test(s)) s = s.replace(/\./g, '').replace(',', '.');
      else s = s.replace(',', '.');
      return /^\d+(\.\d+)?$/.test(s) ? Number(s) : NaN;
    }

    function sorted() {
      const arr = list.slice();
      const desc = k => (a, b) => (b[k] ?? -1) - (a[k] ?? -1);
      switch (ui.sort.value) {
        case 'area': return arr.sort(desc('area'));
        case 'rooms': return arr.sort(desc('rooms'));
        case 'name': return arr.sort((a, b) => a.name.localeCompare(b.name, 'it', { sensitivity: 'base' }));
        default: return arr.sort((a, b) => a.created - b.created);
      }
    }

    const muted = text => h('span', { class: 'muted' }, text);

    function refRow() {
      const house = state.house;
      const rec = state.options.find(o => o.letter === state.recommended);
      const note = rec
        ? `Proposta ${rec.letter}, ${optionTitle(rec)}. Giardino d’inverno come ipotesi condizionata.`
        : 'Casa con guardaroba. Giardino d’inverno come ipotesi condizionata.';
      return h('tr', { class: 'is-ref' },
        h('th', { scope: 'row' },
          h('span', { class: 'house-name' }, show(house && house.name) || 'Casa Margherita'),
          h('span', { class: 'tag' }, 'Riferimento')),
        h('td', { 'data-label': 'Località' }, show(house && house.place) || muted(DASH)),
        h('td', { 'data-label': 'Superficie utile dichiarata' }, h('a', { href: '#aree' }, house?.area || '112 m² utili dichiarati')),
        h('td', { 'data-label': 'Camere reali' }, '1 nella proposta A'),
        h('td', { 'data-label': 'Garage' }, house?.garage || 'Garage separato'),
        h('td', { class: 'note', 'data-label': 'Note' }, note),
        h('td', { class: 'actions' }, h('a', { class: 'btn btn--line btn--small', href: '#casa' }, 'Vedi la decisione')));
    }

    function row(r) {
      const garage = r.garage === 'si' ? 'Sì' : r.garage === 'no' ? 'No' : muted('Non indicato');
      return h('tr', { class: r.id === editing ? 'is-editing' : null },
        h('th', { scope: 'row' }, h('span', { class: 'house-name' }, r.name)),
        h('td', { 'data-label': 'Località' }, r.place || muted(DASH)),
        h('td', { class: 'num', 'data-label': 'Superficie utile dichiarata' },
          r.area == null ? muted('Non indicata') : `${fmtNum(r.area)} m²`),
        h('td', { class: 'num', 'data-label': 'Camere reali' },
          r.rooms == null ? muted('Non indicate') : String(r.rooms)),
        h('td', { 'data-label': 'Garage' }, garage),
        h('td', { class: 'note', 'data-label': 'Note' }, r.notes || muted(DASH), planButtons(r.id)),
        h('td', { class: 'actions' },
          h('button', { type: 'button', class: 'btn btn--line btn--small', 'data-edit': r.id, 'aria-label': `Modifica ${r.name}` }, 'Modifica'),
          h('button', { type: 'button', class: 'btn btn--small btn--danger', 'data-remove': r.id, 'aria-label': `Rimuovi ${r.name}` }, 'Rimuovi')));
    }

    function render() {
      if (!ui) return;
      ui.body.replaceChildren(refRow(), ...sorted().map(row));
      const n = list.length;
      ui.empty.hidden = n > 0;
      ui.tools.hidden = n === 0;
      ui.count.hidden = n === 0;
      ui.count.textContent = n ? String(n) : '';
      if (n) ui.nav.setAttribute('aria-label', `Altre case, ${n === 1 ? 'una inserita' : `${n} inserite`}`);
      else ui.nav.removeAttribute('aria-label');
    }

    const rowButton = (id, kind) => ui.body.querySelector(`[data-${kind}="${CSS.escape(id)}"]`);

    function showErrors(errs) {
      for (const key of ['name', 'area', 'rooms']) {
        const input = ui.form.elements[key];
        const out = $(`[data-err="${key}"]`, ui.form);
        if (errs[key]) {
          input.setAttribute('aria-invalid', 'true');
          out.textContent = errs[key];
        } else {
          input.removeAttribute('aria-invalid');
          out.textContent = '';
        }
      }
    }

    function resetForm() {
      ui.form.reset();
      editing = null;
      ui.form.classList.remove('is-editing');
      ui.title.textContent = 'Aggiungi una casa';
      ui.submit.textContent = 'Aggiungi al confronto';
      ui.cancel.hidden = true;
      showErrors({});
    }

    function onSubmit(e) {
      e.preventDefault();
      const f = ui.form.elements;
      const name = str(f.name.value);
      const place = str(f.place.value);
      const areaRaw = str(f.area.value);
      const roomsRaw = str(f.rooms.value);
      const errs = {};
      let area = null;
      let rooms = null;

      if (!name) errs.name = 'Scrivi un nome: serve a riconoscere la casa nel confronto.';
      if (areaRaw) {
        const n = parseArea(areaRaw);
        if (n > 0) area = n;
        else errs.area = 'Usa solo cifre, con la virgola per i decimali.';
      }
      if (roomsRaw) {
        if (/^\d{1,2}$/.test(roomsRaw)) rooms = Number(roomsRaw);
        else errs.rooms = 'Indica un numero intero di camere.';
      }

      showErrors(errs);
      const firstError = Object.keys(errs)[0];
      if (firstError) {
        ui.msg.textContent = 'Controlla i campi segnalati.';
        f[firstError].focus();
        return;
      }

      const record = {
        name, place, area, rooms,
        garage: str(new FormData(ui.form).get('garage')),
        notes: str(f.notes.value).slice(0, 600),
        updated: Date.now()
      };
      const wasEditing = editing;
      if (wasEditing) {
        const i = list.findIndex(r => r.id === wasEditing);
        if (i > -1) list[i] = { ...list[i], ...record };
      } else {
        list.push({ id: uid(), created: record.updated, ...record });
      }

      const saved = write();
      resetForm();
      render();
      const tail = saved ? '' : ' Il browser non ha permesso di salvarla: resterà solo finché la pagina è aperta.';
      ui.msg.textContent = wasEditing
        ? `Modifiche a «${name}» salvate.${tail}`
        : `«${name}» è stata aggiunta al confronto.${tail}`;

      const btn = wasEditing && rowButton(wasEditing, 'edit');
      if (btn) btn.focus();
      else f.name.focus();
    }

    function startEdit(id) {
      const r = list.find(x => x.id === id);
      if (!r) return;
      const f = ui.form.elements;
      editing = id;
      f.name.value = r.name;
      f.place.value = r.place;
      f.area.value = r.area == null ? '' : fmtNum(r.area);
      f.rooms.value = r.rooms == null ? '' : String(r.rooms);
      f.garage.value = r.garage;
      f.notes.value = r.notes;
      showErrors({});
      ui.form.classList.add('is-editing');
      ui.title.textContent = `Modifica: ${r.name}`;
      ui.submit.textContent = 'Salva modifiche';
      ui.cancel.hidden = false;
      ui.msg.textContent = '';
      render();
      ui.form.scrollIntoView({ block: 'start' });
      f.name.focus({ preventScroll: true });
    }

    function cancelEdit() {
      const id = editing;
      resetForm();
      render();
      ui.msg.textContent = 'Modifica annullata.';
      const btn = id && rowButton(id, 'edit');
      if (btn) btn.focus();
    }

    function remove(id) {
      const r = list.find(x => x.id === id);
      if (!r) return;
      if (!window.confirm(`Rimuovere «${r.name}» dal confronto? I dati sono solo in questo browser e non si potranno recuperare.`)) return;
      const pos = sorted().findIndex(x => x.id === id);
      list = list.filter(x => x.id !== id); forgetPlan(id);
      if (editing === id) resetForm();
      write();
      render();
      ui.msg.textContent = `«${r.name}» rimossa dal confronto.`;
      const rest = sorted();
      const next = rest[Math.min(pos, rest.length - 1)];
      const btn = next && rowButton(next.id, 'edit');
      if (btn) btn.focus();
      else ui.form.elements.name.focus();
    }

    function clearAll() {
      if (!list.length) return;
      if (!window.confirm('Rimuovere tutte le case inserite? I dati sono solo in questo browser e non si potranno recuperare.')) return;
      list.forEach(r=>forgetPlan(r.id)); list = [];
      write();
      resetForm();
      render();
      ui.msg.textContent = 'Tutte le case inserite sono state rimosse.';
      ui.form.elements.name.focus();
    }

    function init() {
      ui = {
        form: $('[data-house-form]'),
        title: $('[data-form-title]'),
        submit: $('[data-submit]'),
        cancel: $('[data-cancel]'),
        msg: $('[data-form-msg]'),
        body: $('[data-houses]'),
        empty: $('[data-empty]'),
        tools: $('[data-tools]'),
        sort: $('[data-sort]'),
        count: $('[data-altre-count]'),
        nav: $('[data-nav-altre]')
      };
      persistent = canStore();
      $('[data-storage-warn]').hidden = persistent;
      list = read();

      ui.form.addEventListener('submit', onSubmit);
      ui.cancel.addEventListener('click', cancelEdit);
      ui.form.addEventListener('keydown', e => {
        if (e.key === 'Escape' && editing) {
          e.preventDefault();
          cancelEdit();
        }
      });
      ui.form.addEventListener('input', e => {
        const field = e.target;
        if (field.getAttribute('aria-invalid') !== 'true') return;
        field.removeAttribute('aria-invalid');
        const out = $(`[data-err="${field.name}"]`, ui.form);
        if (out) out.textContent = '';
      });
      ui.body.addEventListener('click', e => {
        const edit = e.target.closest('[data-edit]');
        const del = e.target.closest('[data-remove]');
        if (edit) startEdit(edit.getAttribute('data-edit'));
        else if (del) remove(del.getAttribute('data-remove'));
      });
      ui.sort.addEventListener('change', () => {
        render();
        say(`Case ordinate per ${ui.sort.selectedOptions[0].text.toLowerCase()}.`);
      });
      $('[data-clear]').addEventListener('click', clearAll);

      // Un'altra scheda dello stesso browser ha modificato l'elenco.
      window.addEventListener('storage', e => {
        if (e.key !== STORE_KEY && e.key !== null) return;
        list = read();
        if (editing && !list.some(r => r.id === editing)) resetForm();
        render();
      });

      render();
    }

    return { init, render };
  })();

  /* ---------- caricamento ---------- */

  async function load() {
    const [cases, audit] = await Promise.allSettled([getJSON(SRC.cases), getJSON(SRC.audit)]);

    let casesOk = false;
    if (cases.status === 'fulfilled') {
      try {
        casesOk = renderCases(cases.value);
      } catch (err) {
        console.error(err);
        failCases(new SyntaxError());
      }
    } else {
      failCases(cases.reason);
    }

    let auditOk = false;
    if (audit.status === 'fulfilled') {
      try {
        renderAudit(audit.value);
        auditOk = true;
      } catch (err) {
        console.error(err);
        failAudit(new SyntaxError());
      }
    } else {
      failAudit(audit.reason);
    }

    heroStatus(casesOk, auditOk);
    Altre.render();
  }

  function init() {
    route();
    initHero();
    initOverlay();
    initDetailPhoto();
    Altre.init();
    document.addEventListener('click', onVariantClick);
    window.addEventListener('hashchange', route);
    window.addEventListener('popstate', onPopState);
    load();
  }

  init();
})();
