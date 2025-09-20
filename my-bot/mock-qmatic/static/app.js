const qs = s => document.querySelector(s);

// Helper to create elements with attributes + children
const el = (tag, attrs = {}, children = []) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") n.className = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === "role") n.setAttribute("role", v);
    else if (k === "ariaLabel") n.setAttribute("aria-label", v);
    else if (v !== undefined && v !== null) n.setAttribute(k, v);
  }
  (Array.isArray(children) ? children : [children]).forEach(c => n.append(c));
  return n;
};

const state = {
  schema: null,
  selected: { sucursal:null, tramite:null, date:null, time:null },
  user: { name:"", id:"", email:"", phone:"" },
  monthIndex: 0
};

async function bootstrap() {
  const res = await fetch('/api/schema' + location.search);
  state.schema = await res.json();

  qs('#pageTitle').textContent = state.schema.title || 'Reserva de cita';
  qs('#cookieText').textContent = state.schema.cookie?.text || 'Usamos cookies.';
  qs('#acceptCookies').textContent = state.schema.cookie?.accept || 'Aceptar';
  qs('#acceptCookies').addEventListener('click', () => qs('#cookie').remove());

  renderAccordion();
  // Step 4 starts disabled until a day with availability is picked
  setStep4Enabled(false);
}

/* ---------- Accordion scaffolding ---------- */
function renderAccordion() {
  const root = qs('#accordion'); root.innerHTML = "";

  root.append(makePanel({
    number: 1, variant: 1, step: 1,
    title: state.schema.sucursal.panel_title,
    subtitle: state.schema.sucursal.subtitle,
    content: renderSucursal, expanded: true
  }));

  root.append(makePanel({
    number: 2, variant: 2, step: 2,
    title: state.schema.tramite.panel_title,
    content: renderTramite
  }));

  root.append(makePanel({
    number: 3, variant: 3, step: 3,
    title: state.schema.fecha_hora.panel_title,
    content: renderFechaHora
  }));

  root.append(makePanel({
    number: 4, variant: 4, step: 4,
    title: state.schema.contacto.panel_title,
    content: renderContacto
  }));
}

function makePanel({number, variant, step, title, subtitle, content, expanded=false}) {
  const panel = el('section', {
    class:'panel',
    'data-variant': String(variant),
    'data-step': String(step),
    'aria-expanded': String(expanded)
  }, []);
  const hdrBtn = el('button', {class:'hdr', role:'button', 'aria-expanded': String(expanded)});
  const left = el('div', {class:'left'});
  left.append(el('div', {class:'badge'}, [String(number)]));
  left.append(el('div', {}, [
    el('div', {style:'color:#fff; font-weight:700'}, [title]),
    subtitle ? el('div', {class:'subtitle'}, [subtitle]) : ''
  ]));
  hdrBtn.append(left, el('div', {class:'chev'}, ['▾']));
  hdrBtn.addEventListener('click', () => {
    if (panel.getAttribute('data-disabled') === 'true') return; // block if disabled
    const cur = panel.getAttribute('aria-expanded') === 'true';
    panel.setAttribute('aria-expanded', String(!cur));
    hdrBtn.setAttribute('aria-expanded', String(!cur));
  });
  const body = el('div', {class:'body'}, []);
  content(body);
  panel.append(hdrBtn, body);
  return panel;
}

/* ---------- Enable/disable step 4 ---------- */
function setStep4Enabled(enabled) {
  const p4 = document.querySelector('.panel[data-step="4"]');
  if (!p4) return;
  const hdr = p4.querySelector('.hdr');
  if (enabled) {
    p4.removeAttribute('data-disabled');
    hdr.removeAttribute('aria-disabled');
  } else {
    p4.setAttribute('data-disabled', 'true');
    p4.setAttribute('aria-expanded', 'false');
    hdr.setAttribute('aria-disabled', 'true');
    hdr.setAttribute('aria-expanded', 'false');
  }
}

function openPanel(n) {
  const panels = document.querySelectorAll('.panel');
  panels.forEach((p, i) => {
    const expanded = (i <= (n-1));
    if (p.getAttribute('data-disabled') === 'true' && expanded && p.getAttribute('data-step') === '4') {
      // don't force-open disabled step 4
      p.setAttribute('aria-expanded', 'false');
      const hdr = p.querySelector('.hdr'); hdr?.setAttribute('aria-expanded', 'false');
      return;
    }
    p.setAttribute('aria-expanded', String(expanded));
    const hdr = p.querySelector('.hdr');
    if (hdr) hdr.setAttribute('aria-expanded', String(expanded));
  });
  qs('#successBox').style.display = 'none';
}

/* ---------- Panel 1: SUCURSAL ---------- */
function renderSucursal(container) {
  const list = el('div', {class:'radio-list', role:'group', ariaLabel: state.schema.sucursal.panel_title}, []);
  (state.schema.sucursal.options||[]).forEach((name, idx) => {
    const id = 'suc_'+idx;
    const row = el('label', {class:'radio-item', for:id});
    const input = el('input', {type:'radio', id, name:'sucursal', value:name});
    input.addEventListener('change', () => { state.selected.sucursal = name; openPanel(2); });
    row.append(input, el('span', {}, [name]));
    list.append(row);
  });
  container.append(list);
}

/* ---------- Panel 2: TRÁMITE ---------- */
function renderTramite(container) {
  if (state.schema.tramite.legend) container.append(el('div', {style:'margin-bottom:8px; color:#555'}, [state.schema.tramite.legend]));
  const list = el('div', {class:'radio-list', role:'group', ariaLabel: state.schema.tramite.panel_title}, []);
  (state.schema.tramite.options||[]).forEach((name, idx) => {
    const id = 'tra_'+idx;
    const row = el('label', {class:'radio-item', for:id});
    const input = el('input', {type:'radio', id, name:'tramite', value:name});
    input.addEventListener('change', () => { state.selected.tramite = name; openPanel(3); });
    row.append(input, el('span', {}, [name]));
    list.append(row);
  });
  container.append(list);
}

/* ---------- Panel 3: FECHA Y HORA ---------- */
function renderFechaHora(container) {
  container.innerHTML = "";

  // Intro
  container.append(el('div', {class:'monthbar'}, [state.schema.fecha_hora.intro]));

  // Nav
  const nav = el('div', {class:'monthnav'});
  const prev = el('button', {role:'button', ariaLabel:'Anterior', class:'btn', onClick:() => { changeMonth(-1); renderFechaHora(container); }}, ['‹']);
  const next = el('button', {role:'button', ariaLabel:'Siguiente', class:'btn', onClick:() => { changeMonth(+1); renderFechaHora(container); }}, ['›']);
  const label = el('div', {}, [currentMonth().label]);
  nav.append(prev, label, next);
  container.append(nav);

  // Weekdays
  const weekdays = ["lu","ma","mi","ju","vi","sá","do"];
  const wk = el('div', {class:'weekrow'}, []);
  weekdays.forEach(w => wk.append(el('div', {}, [w])));
  container.append(wk);

  // Days grid
  const month = currentMonth();
  const enabled = new Set((month.enabled_days||[]).map(String)); // empty → all enabled
  const grid = el('div', {class:'daysgrid', role:'grid'}, []);
  const daysInMonth = new Date(month.year, month.month, 0).getDate();
  for (let d=1; d<=daysInMonth; d++) {
    const dayStr = String(d).padStart(2,'0');
    const dateISO = `${month.year}-${String(month.month).padStart(2,'0')}-${dayStr}`;
    const clickable = enabled.size === 0 || enabled.has(String(d));

    const btnAttrs = {
      class:'day',
      role:'button',
      'data-date': dateISO,
      'ariaLabel': `Día ${d}`,
      onClick: clickable ? () => {
        state.selected.date = dateISO;
        state.selected.time = null;
        markSelectedDay(dateISO);        // highlight day
        const hasSlots = renderTimeSlots(container); // also (re)builds slots
        setStep4Enabled(hasSlots);
        if (hasSlots) openPanel(4);
        updatePickSummary(container);    // show summary
      } : undefined
    };
    if (!clickable) btnAttrs.disabled = true;

    const btn = el('button', btnAttrs, [dayStr]);
    if (state.selected.date === dateISO) btn.classList.add('selected');
    grid.append(btn);
  }
  container.append(grid);

  // Slots / "no slots" message for previously-selected date
  const has = renderTimeSlots(container);
  setStep4Enabled(Boolean(has && state.selected.date));
  updatePickSummary(container);          // keep summary consistent
}

function currentMonth() {
  const months = state.schema.fecha_hora.months || [];
  if (months.length === 0) return { year: 2025, month: 9, label: "septiembre 2025", enabled_days: [], times_by_date: {} };
  return months[Math.max(0, Math.min(state.monthIndex, months.length - 1))];
}
function changeMonth(delta) {
  const months = state.schema.fecha_hora.months || [];
  if (months.length === 0) return;
  state.monthIndex = Math.max(0, Math.min(state.monthIndex + delta, months.length - 1));
  state.selected.date = null;
  state.selected.time = null;
}

function renderTimeSlots(container) {
  container.querySelectorAll('.slots, .muted').forEach(n => n.remove());

  // Remove previous summary (we re-add below)
  const oldSummary = container.querySelector('.pick-summary');
  if (oldSummary) oldSummary.remove();

  if (!state.selected.date) return false;

  const flags = state.schema.flags || {};
  const month = currentMonth();
  const timesMap = month.times_by_date || {};
  const times = flags.no_slots ? [] : (timesMap[state.selected.date] || []);

  if (times.length === 0) {
    container.append(el('div', {class:'muted'}, [state.schema.fecha_hora.no_slots_msg]));
    return false;
  }

  const wrap = el('div', {class:'slots'}, []);
  times.forEach(t => {
    const b = el('button', {
      class:'slotbtn' + (state.selected.time === t ? ' selected' : ''),
      role:'button',
      'data-time': t,
      onClick: () => {
        state.selected.time = t;
        markSelectedTime(t);               // highlight time
        openPanel(4);
        updatePickSummary(container);      // show summary
      }
    }, [t]);
    wrap.append(b);
  });
  container.append(wrap);
  return true;
}

/* ---------- Helpers to mark selected items ---------- */
function markSelectedDay(dateISO) {
  document.querySelectorAll('.day').forEach(b => b.classList.remove('selected'));
  const btn = document.querySelector(`.day[data-date="${dateISO}"]`);
  if (btn) btn.classList.add('selected');
}
function markSelectedTime(timeStr) {
  document.querySelectorAll('.slotbtn').forEach(b => b.classList.remove('selected'));
  const btn = document.querySelector(`.slotbtn[data-time="${timeStr}"]`);
  if (btn) btn.classList.add('selected');
}

/* ---------- Tiny summary under the calendar ---------- */
function updatePickSummary(container) {
  const old = container.querySelector('.pick-summary');
  if (old) old.remove();

  const hasDate = !!state.selected.date;
  const hasTime = !!state.selected.time;

  if (!hasDate && !hasTime) return;

  const wrap = el('div', {class:'pick-summary'});
  if (hasDate) wrap.append(el('span', {class:'pill'}, [`Fecha: ${state.selected.date}`]));
  if (hasTime) wrap.append(el('span', {class:'pill'}, [`Hora: ${state.selected.time}`]));
  container.append(wrap);
}

/* ---------- Panel 4: CONTACTO ---------- */
function renderContacto(container) {
  container.innerHTML = "";
  const f = state.schema.contacto.fields || [];
  f.forEach(field => {
    const row = el('div', {class:'row'});
    const label = el('label', {}, [field.label]); label.htmlFor = 'input_'+field.name;
    const input = el('input', {id:'input_'+field.name, placeholder: field.placeholder || field.label});
    input.addEventListener('input', e => state.user[field.name] = e.target.value);
    row.append(label, input);
    container.append(row);
  });

  const confirm = el('div', {class:'confirm'});
  confirm.append(el('button', {
    class:'btn primary',
    role:'button',
    ariaLabel: state.schema.contacto.confirm_text || 'Confirmar',
    onClick: onConfirm
  }, [state.schema.contacto.confirm_text || 'Confirmar']));
  container.append(confirm);
}

function onConfirm() {
  for (const f of state.schema.contacto.fields) {
    if (!state.user[f.name]) { alert('Falta ' + f.label); return; }
  }
  // Optional: enforce a time selection if your flow requires it
  // if (!state.selected.time) { alert('Seleccione una hora.'); return; }

  const s = state.schema;
  qs('#successTitle').textContent = s.contacto.success_title;
  const msg = (s.contacto.success_msg || '')
    .replace('{DATE}', state.selected.date || '')
    .replace('{TIME}', state.selected.time || '')
    .replace('{SERVICE}', state.selected.tramite || '');
  qs('#successMsg').textContent = msg;
  qs('#successBox').style.display = 'block';
}

bootstrap();