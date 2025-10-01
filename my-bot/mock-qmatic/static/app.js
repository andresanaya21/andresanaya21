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
  (Array.isArray(children) ? children : [children]).forEach(c => {
    if (c !== undefined && c !== null && c !== '') n.append(c);
  });
  return n;
};

const state = {
  schema: null,
  selected: { sucursal:null, tramite:null, date:null, time:null },
  user: { name:"", lastname:"", id:"", email:"", email_confirm:"", phone_cc:"+34", phone:"", phone_confirm:"", notes:"", consent:false },
  monthIndex: 0,
  mode: 'book' // 'book' | 'notify'
};

async function bootstrap() {
  // IMPORTANT: do NOT forward no_slots from the URL accidentally
  const res = await fetch('/api/schema');
  state.schema = await res.json();

  qs('#pageTitle').textContent = state.schema.title || 'Reserva de cita';
  qs('#cookieText').textContent = state.schema.cookie?.text || 'Usamos cookies.';
  qs('#acceptCookies').textContent = state.schema.cookie?.accept || 'Aceptar';
  qs('#acceptCookies').addEventListener('click', () => qs('#cookie').remove());

  renderAccordion();
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
  });
  const hdrBtn = el('button', {class:'hdr', role:'button', 'aria-expanded': String(expanded)});
  const left = el('div', {class:'left'});
  left.append(el('div', {class:'badge'}, [String(number)]));
  left.append(el('div', {}, [
    el('div', {style:'color:#fff; font-weight:700'}, [title]),
    subtitle ? el('div', {class:'subtitle'}, [subtitle]) : ''
  ]));
  hdrBtn.append(left, el('div', {class:'chev'}, ['▾']));
  hdrBtn.addEventListener('click', () => {
    if (panel.getAttribute('data-disabled') === 'true') return;
    const cur = panel.getAttribute('aria-expanded') === 'true';
    panel.setAttribute('aria-expanded', String(!cur));
    hdrBtn.setAttribute('aria-expanded', String(!cur));
  });
  const body = el('div', {class:'body'});
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
  state.mode = 'book';

  container.append(el('div', {class:'monthbar'}, [state.schema.fecha_hora.intro]));

  const nav = el('div', {class:'monthnav'});
  const prev = el('button', {role:'button', ariaLabel:'Anterior', class:'btn', onClick:() => { changeMonth(-1); renderFechaHora(container); }}, ['‹']);
  const next = el('button', {role:'button', ariaLabel:'Siguiente', class:'btn', onClick:() => { changeMonth(+1); renderFechaHora(container); }}, ['›']);
  const label = el('div', {}, [currentMonth().label]);
  nav.append(prev, label, next);
  container.append(nav);

  const weekdays = ["lu","ma","mi","ju","vi","sá","do"];
  const wk = el('div', {class:'weekrow'}, []);
  weekdays.forEach(w => wk.append(el('div', {}, [w])));
  container.append(wk);

  const month = currentMonth();
  // undefined/null -> all enabled; empty [] -> none enabled
  const raw = month.enabled_days;
  const enableAll = (raw == null);
  const enabled = new Set((raw || []).map(d => String(parseInt(d, 10))));
  const grid = el('div', {class:'daysgrid', role:'grid'}, []);
  const daysInMonth = new Date(month.year, month.month, 0).getDate();
  for (let d=1; d<=daysInMonth; d++) {
    const dayStr = String(d).padStart(2,'0');
    const dateISO = `${month.year}-${String(month.month).padStart(2,'0')}-${dayStr}`;
    const clickable = enableAll ? true : enabled.has(String(d));
    const btnAttrs = {
      class:'day',
      role:'button',
      'data-date': dateISO,
      'ariaLabel': `Día ${d}`,
      onClick: clickable ? () => {
        state.selected.date = dateISO;
        state.selected.time = null;
        markSelectedDay(dateISO);
        const hasSlots = renderTimeSlots(container);
        setStep4Enabled(hasSlots);
        if (hasSlots) openPanel(4);
        updatePickSummary(container);
      } : undefined
    };
    if (!clickable) btnAttrs.disabled = true;
    const btn = el('button', btnAttrs, [dayStr]);
    if (state.selected.date === dateISO) btn.classList.add('selected');
    grid.append(btn);
  }
  container.append(grid);

  const has = renderTimeSlots(container);
  setStep4Enabled(Boolean(has && state.selected.date));
  updatePickSummary(container);
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

/* ---------- Build slots or the "no availability" box ---------- */
function renderTimeSlots(container) {
  container.querySelectorAll('.slots, .muted, .emptybox, .pick-summary').forEach(n => n.remove());
  if (!state.selected.date) return false;

  const flags = state.schema.flags || {};
  const month = currentMonth();
  const timesMap = month.times_by_date || {};
  let times = flags.no_slots ? [] : (timesMap[state.selected.date] || []);

  // Client fallback: if the selected date is ENABLED but has no times, show default_times
  if (!flags.no_slots && times.length === 0) {
    const raw = month.enabled_days;
    const enableAll = (raw == null);
    const enabled = new Set((raw || []).map(d => String(parseInt(d, 10))));
    const dayNum = String(parseInt(state.selected.date.slice(-2), 10));
    if (enableAll || enabled.has(dayNum)) {
      times = (state.schema.fecha_hora.default_times || ["09:00","09:20","09:40","10:00","10:20","10:40"]);
    }
  }

  if (times.length === 0) {
    state.selected.time = null;
    const box = el('div', {class:'emptybox'}, [
      el('div', {class:'empty-title'}, [state.schema.fecha_hora.no_slots_title || 'Sin disponibilidad']),
      el('div', {class:'empty-msg'}, [
        state.schema.fecha_hora.no_slots_msg
          || 'No hay horas disponibles para el número seleccionado de personas y trámite'
      ]),
      el('div', {class:'actions'}, [
        el('button', {class:'btn', onClick: onFindFirstAvailable}, [state.schema.fecha_hora.find_first_btn || 'Buscar primera fecha disponible']),
        el('button', {class:'btn primary', onClick: onNotifyMe}, [state.schema.fecha_hora.notify_btn || 'Avisarme cuando haya citas'])
      ])
    ]);
    container.append(box);
    return false;
  }

  const wrap = el('div', {class:'slots'}, []);
  times.forEach(t => {
    const b = el('button', {
      class:'slotbtn' + (state.selected.time === t ? ' selected' : ''),
      role:'button',
      'data-time': t,
      onClick: () => {
        state.mode = 'book';
        state.selected.time = t;
        markSelectedTime(t);
        openPanel(4);
        setStep4Enabled(true);
        updatePickSummary(container);
        // Also re-evaluate Step 4 button enabled state
        reevaluateFinishButtons();
      }
    }, [t]);
    wrap.append(b);
  });
  container.append(wrap);
  return true;
}

/* ---------- Actions when no availability ---------- */
function onFindFirstAvailable() {
  const months = state.schema.fecha_hora.months || [];
  let startIdx = state.monthIndex;

  for (let m = startIdx; m < months.length; m++) {
    const mobj = months[m];
    const dates = Object.keys(mobj.times_by_date || {}).sort();
    for (const dateISO of dates) {
      const slots = (mobj.times_by_date || {})[dateISO] || [];
      if (slots.length > 0) {
        state.monthIndex = m;
        state.selected.date = dateISO;
        state.selected.time = slots[0];
        state.mode = 'book';
        const p3Body = document.querySelector('.panel[data-step="3"] .body');
        if (p3Body) renderFechaHora(p3Body);
        markSelectedDay(dateISO);
        markSelectedTime(state.selected.time);
        setStep4Enabled(true);
        openPanel(4);
        reevaluateFinishButtons();
        return;
      }
    }
  }
  alert(state.schema.fecha_hora.no_any_availability || 'No se han encontrado citas en los meses cargados.');
}

function onNotifyMe() { state.mode = 'notify'; setStep4Enabled(true); openPanel(4); }

/* ---------- Helpers ---------- */
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

/* ---------- Summary under calendar ---------- */
function updatePickSummary(container) {
  const old = container.querySelector('.pick-summary');
  if (old) old.remove();
  const hasDate = !!state.selected.date;
  const hasTime = !!state.selected.time;
  if (!hasDate && !hasTime && state.mode !== 'notify') return;

  const wrap = el('div', {class:'pick-summary'});
  if (state.mode === 'notify') {
    wrap.append(el('span', {class:'pill'}, ['Modo: Avisarme']));
    if (hasDate) wrap.append(el('span', {class:'pill'}, [`Fecha elegida: ${state.selected.date}`]));
  } else {
    if (hasDate) wrap.append(el('span', {class:'pill'}, [`Fecha: ${state.selected.date}`]));
    if (hasTime) wrap.append(el('span', {class:'pill'}, [`Hora: ${state.selected.time}`]));
  }
  container.append(wrap);
}

/* ---------- VALIDATION + FINISH BUTTONS ---------- */

// Return true if contact form is valid for the current mode
function isContactValid() {
  const cfg = state.schema.contacto;

  // Required fields
  for (const f of (cfg.fields || [])) {
    if (state.mode === 'notify') {
      // For notify mode, require: name, email (+ confirm), consent
      const notifyRequired = new Set(['name', 'email', 'email_confirm']);
      if (!notifyRequired.has(f.name)) continue;
    }
    if (f.required && !state.user[f.name]) return false;
  }

  // Email match
  if (state.user.email || state.user.email_confirm) {
    if (state.user.email !== state.user.email_confirm) return false;
  }

  // Phone match (only in book mode if fields exist)
  if (state.mode === 'book' && (state.user.phone || state.user.phone_confirm)) {
    if (state.user.phone !== state.user.phone_confirm) return false;
  }

  // Consent
  if (state.schema.contacto.consent?.required && !state.user.consent) return false;

  // In book mode we also need a picked time
  if (state.mode === 'book' && !state.selected.time) return false;

  return true;
}

// Enable/disable & show/hide the final action button(s)
function reevaluateFinishButtons() {
  const btn = qs('#btnAceptar');       // main finish button
  const btnAlt = qs('#btnCogerCita');  // optional alt label (hidden)
  const enabled = isContactValid();

  [btn, btnAlt].forEach(b => {
    if (!b) return;
    if (enabled) {
      b.removeAttribute('disabled');
      b.removeAttribute('aria-disabled');
    } else {
      b.setAttribute('disabled', 'true');
      b.setAttribute('aria-disabled', 'true');
    }
  });
}

/* ---------- Panel 4: CONTACTO (upgraded) ---------- */
function renderContacto(container) {
  container.innerHTML = "";
  const cfg = state.schema.contacto;

  // Build inputs
  (cfg.fields || []).forEach(field => {
    const row = el('div', {class:'row' + (field.rowClass ? ' '+field.rowClass : '')});
    const labelText = field.required ? `${field.label} *` : field.label;

    const label = el('label', {}, [labelText]); label.htmlFor = 'input_'+field.name;
    let input;
    if (field.type === 'textarea') {
      input = el('textarea', {id:'input_'+field.name, placeholder: field.placeholder || field.label, rows: field.rows || 3});
    } else {
      input = el('input', {
        id:'input_'+field.name,
        placeholder: field.placeholder || field.label,
        type: field.type || 'text',
        value: field.default || ''
      });
    }
    input.addEventListener('input', e => {
      state.user[field.name] = e.target.value;
      // auto-copy confirm fields if empty
      if (field.name === 'email') {
        const conf = qs('#input_email_confirm');
        if (conf && !conf.value) conf.value = e.target.value;
      }
      if (field.name === 'phone') {
        const confp = qs('#input_phone_confirm');
        if (confp && !confp.value) confp.value = e.target.value;
      }
      // Each change may unlock the finish button
      reevaluateFinishButtons();
    });

    // initialize defaults
    if (field.default) {
      state.user[field.name] = field.default;
    }

    row.append(label, input);
    container.append(row);
  });

  // Consent checkbox
  if (cfg.consent) {
    const c = cfg.consent;
    const row = el('div', {class:'row'});
    const id = 'input_consent';
    const box = el('input', {id, type:'checkbox'});
    box.addEventListener('change', e => { state.user.consent = e.target.checked; reevaluateFinishButtons(); });
    const lab = el('label', {for:id}, [c.label || 'Estoy informado/a sobre el tratamiento de mis datos personales']);
    row.append(box, lab);
    container.append(row);
  }

  // --- Final action area ---
  const confirm = el('div', {class:'confirm'});

  // Decide which label to show (simulate real site variance)
  const finishVariants = ['ACEPTAR', 'Coger cita'];
  const chosen = finishVariants[Math.floor(Math.random() * finishVariants.length)];
  const chosenForNotify = cfg.notify_confirm_text || 'Guardar aviso';

  // MAIN finish button (id = btnAceptar)
  const mainBtn = el('button', {
    id: 'btnAceptar',
    class:'btn primary',
    role:'button',
    ariaLabel: state.mode === 'notify' ? chosenForNotify : chosen,
    onClick: onConfirm,
    disabled: 'true',
    'aria-disabled': 'true'
  }, [state.mode === 'notify' ? chosenForNotify : chosen]);

  // Optional hidden alt variant (helps testing different labels if you want to toggle it in dev tools)
  const altLabel = (chosen === 'ACEPTAR') ? 'Coger cita' : 'ACEPTAR';
  const altBtn = el('button', {
    id: 'btnCogerCita',
    class:'btn primary',
    role:'button',
    style:'display:none', // hidden by default
    ariaLabel: altLabel,
    onClick: onConfirm,
    disabled: 'true',
    'aria-disabled': 'true'
  }, [altLabel]);

  confirm.append(mainBtn, altBtn);
  container.append(confirm);

  // Evaluate once on render (covers defaults like +34)
  reevaluateFinishButtons();
}

function onConfirm() {
  const cfg = state.schema.contacto;

  // Validate required fields
  for (const f of cfg.fields) {
    if (f.required && !state.user[f.name]) { alert('Falta ' + f.label); return; }
  }
  // Match email + confirm
  if (state.user.email && state.user.email_confirm && state.user.email !== state.user.email_confirm) {
    alert('El correo de confirmación no coincide.'); return;
  }
  // Match phone + confirm
  if (state.user.phone && state.user.phone_confirm && state.user.phone !== state.user.phone_confirm) {
    alert('El número de móvil de confirmación no coincide.'); return;
  }
  // Consent
  if (cfg.consent?.required && !state.user.consent) {
    alert('Debe aceptar el tratamiento de datos personales.'); return;
  }

  const s = state.schema;
  if (state.mode === 'notify') {
    qs('#successTitle').textContent = s.contacto.notify_success_title || 'Aviso registrado';
    const msg = (s.contacto.notify_success_msg || 'Te avisaremos cuando haya citas disponibles — {SERVICE}.')
      .replace('{SERVICE}', state.selected.tramite || '');
    qs('#successMsg').textContent = msg;
    qs('#successBox').style.display = 'block';
    return;
  }

  if (!state.selected.time) { alert('Seleccione una hora.'); return; }

  qs('#successTitle').textContent = s.contacto.success_title || 'Confirmación de cita';
  const msg = (s.contacto.success_msg || 'Cita confirmada para {DATE} a las {TIME} — {SERVICE}')
    .replace('{DATE}', state.selected.date || '')
    .replace('{TIME}', state.selected.time || '')
    .replace('{SERVICE}', state.selected.tramite || '');
  qs('#successMsg').textContent = msg;
  qs('#successBox').style.display = 'block';
}

bootstrap();