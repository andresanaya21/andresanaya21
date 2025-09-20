const qs = s => document.querySelector(s);
const el = (tag, attrs={}, children=[]) => {
  const n = document.createElement(tag);
  for (const [k,v] of Object.entries(attrs)) {
    if (k === "class") n.className = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else if (k === "role") n.setAttribute("role", v);
    else if (k === "ariaLabel") n.setAttribute("aria-label", v);
    else n.setAttribute(k, v);
  }
  for (const c of (Array.isArray(children)?children:[children])) n.append(c);
  return n;
};

const state = {
  schema: null,
  selected: { sucursal:null, tramite:null, date:null, time:null },
  user: { name:"", id:"", email:"", phone:"" }
};

async function bootstrap() {
  const res = await fetch('/api/schema' + location.search);
  state.schema = await res.json();

  qs('#pageTitle').textContent = state.schema.title || 'Reserva de cita';

  // cookie
  qs('#cookieText').textContent = state.schema.cookie?.text || 'Usamos cookies.';
  qs('#acceptCookies').textContent = state.schema.cookie?.accept || 'Aceptar';
  qs('#acceptCookies').addEventListener('click', () => qs('#cookie').remove());

  renderAccordion();
}

function renderAccordion() {
  const root = qs('#accordion'); root.innerHTML = "";

  // Panel 1 — SUCURSAL
  root.append(makePanel({
    number: 1,
    variant: 1,
    title: state.schema.sucursal.panel_title,
    subtitle: state.schema.sucursal.subtitle,
    content: renderSucursal,
    expanded: true
  }));

  // Panel 2 — TRÁMITE
  root.append(makePanel({
    number: 2,
    variant: 2,
    title: state.schema.tramite.panel_title,
    content: renderTramite
  }));

  // Panel 3 — FECHA Y HORA
  root.append(makePanel({
    number: 3,
    variant: 3,
    title: state.schema.fecha_hora.panel_title,
    content: renderFechaHora
  }));

  // Panel 4 — CONTACTO
  root.append(makePanel({
    number: 4,
    variant: 4,
    title: state.schema.contacto.panel_title,
    content: renderContacto
  }));
}

function makePanel({number, variant, title, subtitle, content, expanded=false}) {
  const panel = el('section', {class:'panel', 'data-variant': String(variant), 'aria-expanded': String(expanded)}, []);
  const hdrBtn = el('button', {class:'hdr', role:'button', 'aria-expanded': String(expanded)});
  const left = el('div', {class:'left'});
  left.append(el('div', {class:'badge'}, [String(number)]));
  left.append(el('div', {}, [
    el('div', {style:'color:#fff; font-weight:700'}, [title]),
    subtitle ? el('div', {class:'subtitle'}, [subtitle]) : ''
  ]));
  hdrBtn.append(left, el('div', {class:'chev'}, ['▾']));
  hdrBtn.addEventListener('click', () => {
    const cur = panel.getAttribute('aria-expanded') === 'true';
    panel.setAttribute('aria-expanded', String(!cur));
    hdrBtn.setAttribute('aria-expanded', String(!cur));
  });

  const body = el('div', {class:'body'}, []);
  content(body); // inject
  panel.append(hdrBtn, body);
  return panel;
}

// Panel bodies
function renderSucursal(container) {
  const opts = state.schema.sucursal.options || [];
  const list = el('div', {class:'radio-list', role:'group', ariaLabel: state.schema.sucursal.panel_title}, []);
  opts.forEach((name, idx) => {
    const id = 'suc_'+idx;
    const row = el('label', {class:'radio-item', for:id});
    const input = el('input', {type:'radio', id, name:'sucursal', value:name});
    input.addEventListener('change', () => {
      state.selected.sucursal = name;
      // open next panel
      openPanel(2);
    });
    row.append(input, el('span', {}, [name]));
    list.append(row);
  });
  container.append(list);
}

function renderTramite(container) {
  if (state.schema.tramite.legend) container.append(el('div', {style:'margin-bottom:8px; color:#555'}, [state.schema.tramite.legend]));
  const list = el('div', {class:'radio-list', role:'group', ariaLabel: state.schema.tramite.panel_title}, []);
  (state.schema.tramite.options||[]).forEach((name, idx) => {
    const id = 'tra_'+idx;
    const row = el('label', {class:'radio-item', for:id});
    const input = el('input', {type:'radio', id, name:'tramite', value:name});
    input.addEventListener('change', () => {
      state.selected.tramite = name;
      openPanel(3);
    });
    row.append(input, el('span', {}, [name]));
    list.append(row);
  });
  container.append(list);
}

function renderFechaHora(container) {
  container.append(el('div', {class:'monthbar'}, [state.schema.fecha_hora.intro]));
  const nav = el('div', {class:'monthnav'});
  nav.append(
    el('button', {role:'button', 'ariaLabel':'Anterior', class:'btn'}, ['‹']),
    el('div', {}, [state.schema.fecha_hora.month_label]),
    el('button', {role:'button', 'ariaLabel':'Siguiente', class:'btn'}, ['›'])
  );
  container.append(nav);

  const weekdays = el('div', {class:'weekrow'}, []);
  (state.schema.fecha_hora.weekdays||[]).forEach(w => weekdays.append(el('div', {}, [w])));
  container.append(weekdays);

  const enabled = new Set(state.schema.fecha_hora.enabled_days || []);
  const grid = el('div', {class:'daysgrid', role:'grid'}, []);
  for (let d=1; d<=30; d++) {
    const day = String(d).padStart(2,'0');
    const isEnabled = enabled.has(String(d));
    const btn = el('button', {
      class:'day',
      role:'button',
      "ariaLabel": `Día ${d}`,
      disabled: isEnabled ? undefined : true,
      onClick: isEnabled ? () => {
        state.selected.date = `2025-09-${day}`;
        // show slots below calendar
        renderTimeSlots(container);
      } : undefined
    }, [day]);
    grid.append(btn);
  }
  container.append(grid);

  // initial slots (none until a date picked)
  renderTimeSlots(container);
}

function renderTimeSlots(container) {
  // remove prior slots area if present
  container.querySelectorAll('.slots, .muted').forEach(n => n.remove());

  const flags = state.schema.flags || {};
  const times = state.schema.fecha_hora.times || [];

  if (!state.selected.date) return;

  if (flags.no_slots || times.length === 0) {
    container.append(el('div', {class:'muted'}, [state.schema.fecha_hora.no_slots_msg]));
    return;
  }

  const wrap = el('div', {class:'slots'}, []);
  times.forEach(t => {
    const b = el('button', {class:'slotbtn', role:'button', onClick:() => {
      state.selected.time = t;
      openPanel(4);
    }}, [t]);
    wrap.append(b);
  });
  container.append(wrap);
}

function renderContacto(container) {
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
    'ariaLabel': state.schema.contacto.confirm_text || 'Confirmar',
    onClick: onConfirm
  }, [state.schema.contacto.confirm_text || 'Confirmar']));
  container.append(confirm);
}

function openPanel(n) {
  // n is the panel number (1..4)
  const panels = document.querySelectorAll('.panel');
  panels.forEach((p, i) => {
    const expanded = (i <= (n-1)); // open current and previous
    p.setAttribute('aria-expanded', String(expanded));
    p.querySelector('.hdr').setAttribute('aria-expanded', String(expanded));
  });
  // ensure success box hidden if navigating
  qs('#successBox').style.display = 'none';
}

function onConfirm() {
  // simple required validation
  for (const f of state.schema.contacto.fields) {
    if (!state.user[f.name]) { alert('Falta ' + f.label); return; }
  }
  // show success
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
