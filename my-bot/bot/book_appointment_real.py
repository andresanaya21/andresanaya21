import os, re, sys, time
from pathlib import Path
from playwright.sync_api import Playwright, sync_playwright

# ======================
# CONFIG
# ======================
BASE_URL = os.getenv("BASE_URL", "https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/")
TARGET_TRAMITE = os.getenv("TARGET_TRAMITE", "")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
SLOW_MO_MS = int(os.getenv("SLOW_MO_MS", "120"))
MAX_MONTHS_TO_SCAN = int(os.getenv("MAX_MONTHS_TO_SCAN", "2"))  # current + next
DEFAULT_TIMEOUT_MS = int(os.getenv("DEFAULT_TIMEOUT_MS", "20000"))
RECORD_VIDEO = os.getenv("RECORD_VIDEO", "true").lower() == "true"

CONTACT = {
    "name":           os.getenv("CONTACT_NAME",          ""),
    "lastname":       os.getenv("CONTACT_LASTNAME",      ""),
    "id":             os.getenv("CONTACT_ID",            ""),
    "email":          os.getenv("CONTACT_EMAIL",         ""),
    "email_confirm":  os.getenv("CONTACT_EMAIL_CONFIRM", ""),
    "phone_cc":       os.getenv("CONTACT_PHONE_CC",      ""),
    "phone":          os.getenv("CONTACT_PHONE",         ""),
    "phone_confirm":  os.getenv("CONTACT_PHONE_CONFIRM", ""),
    "notes":          os.getenv("CONTACT_NOTES",         ""),
    "consent":        os.getenv("CONTACT_CONSENT",       "true").lower() == "true",
}

# ==============
# Utilities
# ==============
def validate_config():
    errs = []
    if not TARGET_TRAMITE.strip():
        errs.append("TARGET_TRAMITE must be set.")
    for k in ("name", "lastname", "id", "email", "email_confirm", "phone", "phone_confirm"):
        if not CONTACT.get(k):
            errs.append(f"CONTACT_{k.upper()} must be set.")
    if CONTACT.get("email") != CONTACT.get("email_confirm"):
        errs.append("Email and email_confirm must match.")
    if CONTACT.get("phone") != CONTACT.get("phone_confirm"):
        errs.append("Phone and phone_confirm must match.")
    if errs:
        for e in errs: print("Config error:", e, file=sys.stderr)
        sys.exit(64)

def rx_contains(text):  # case-insensitive “contains” regex with whitespace tolerance
    return re.compile(re.sub(r"\s+", r"\\s+", text.strip()), re.I)

def save(page, name):
    Path("artifacts").mkdir(exist_ok=True)
    try: page.screenshot(path=f"artifacts/{name}.png", full_page=True)
    except Exception: pass

def wait_for_app(page, url, timeout_s=90):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            if page.content(): return True
        except Exception: pass
        time.sleep(0.5)
    return False

def dismiss_cookies(page):
    for sel in ("#acceptCookies","button:has-text('Aceptar')","button:has-text('ACEPTAR')",
                "[aria-label*='Aceptar' i]","button:has-text('OK')","button:has-text('De acuerdo')"):
        try:
            b = page.locator(sel)
            if b.count() and b.first.is_visible():
                try: b.first.click()
                except Exception:
                    try: page.evaluate("(el)=>el && el.click && el.click()", b.first)
                    except Exception: pass
                break
        except Exception: pass

def _click_like_human(page, handle):
    try: page.evaluate("(el)=>el && el.scrollIntoView({block:'center'})", handle)
    except Exception: pass
    try:
        handle.click(timeout=2000)
        return True
    except Exception:
        try:
            page.evaluate("(el)=>el && el.click && el.click()", handle)
            return True
        except Exception:
            try:
                box = handle.bounding_box()
                if not box: return False
                cx, cy = box["x"] + box["width"]/2, box["y"] + box["height"]/2
                page.mouse.click(cx, cy)
                return True
            except Exception:
                return False

# ==========
# Step 1
# ==========
def click_first_sucursal(page):
    hdr = page.locator(".hdr, button").filter(has_text=re.compile(r"SELECCIONAR\s+(SUCURSAL|CENTRO|OFICINA)", re.I)).first
    if hdr.count():
        try:
            if (hdr.get_attribute("aria-expanded") or "").lower() == "false":
                hdr.click()
        except Exception: pass

    radios = page.locator('input[type="radio"][name="sucursal"]')
    if radios.count():
        radios.first.check(); return

    rb = page.get_by_role("radio")
    if rb.count():
        rb.first.check(); return

    cb = page.get_by_role("combobox").first
    if cb.count():
        cb.click(); page.get_by_role("option").first.click(); return

    lab = page.locator("label.radio-item, label").first
    if lab.count():
        try: lab.click()
        except Exception:
            try: lab.locator("input").first.check()
            except Exception: pass
        return

    save(page, "step1_failed")
    raise RuntimeError("Step 1 not found")

# ==========
# Step 2
# ==========
def select_tramite(page, tramite_text):
    step2 = page.locator("section, div").filter(has_text=re.compile(r"SELECCIONAR\s+TR[ÁA]MITE", re.I)).first
    if step2.count():
        try:
            if (step2.get_attribute("aria-expanded") or "").lower() == "false":
                step2.locator(".hdr, button, [role='button']").first.click()
        except Exception: pass

    tgt = rx_contains(tramite_text)

    lab = page.locator("label.radio-item, label").filter(has_text=tgt).first
    if lab.count():
        try: lab.click()
        except Exception:
            lab.locator("input[type=radio]").first.check()
        return

    combo = page.get_by_role("combobox").first
    if not combo.count():
        combo = page.get_by_role("button").filter(has_text=re.compile("Seleccionar\\s+Tr[áa]mite|Tr[áa]mite", re.I)).first
    if combo.count():
        combo.click()
        opt = page.get_by_role("option", name=tgt).first
        if not opt.count():
            opt = page.locator("[role='listbox'] [role='option'], .mat-option-text").filter(has_text=tgt).first
        if opt.count():
            opt.click(); return

    li = page.locator("li, .mat-option, [role='option']").filter(has_text=tgt).first
    if li.count():
        li.click(); return

    save(page, "select_tramite_failed")
    raise RuntimeError("Step 2 (trámite) not found")

# ==========
# Step 3 (date & hour)
# ==========
TIME_RX = re.compile(r"\b([01]?\d|2[0-3]):[0-5]\d\b")
def _parse_time_to_minutes(text):
    m = TIME_RX.search(text or "")
    if not m: return None
    hh, mm = m.group(0).split(":")
    try: return int(hh) * 60 + int(mm)
    except Exception: return None

def _visible_slots(root):
    return root.locator(
        ".slots .slotbtn, .slotbtn, [data-time], [data-slot], "
        ".time-slot button, .times button, "
        ".mat-chip, .mat-mdc-chip, .chip, .hour, "
        "button, a, [role='button']"
    )

def _wait_for_any_slot(root, timeout_s=6):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        loc = _visible_slots(root)
        cnt = loc.count()
        for i in range(min(50, cnt or 0)):
            b = loc.nth(i)
            try:
                if b.is_visible():
                    txt = (b.inner_text() or "").strip()
                    if TIME_RX.search(txt) or b.get_attribute("data-time"):
                        return True
            except Exception: pass
        time.sleep(0.05)
    return False

def _candidate_days(page):
    selectors = [
        ".daysgrid button:not([disabled])",
        ".daysgrid .day:not([disabled])",
        ".mat-calendar-body-cell:not(.mat-calendar-body-disabled)",
        "button.mat-calendar-body-cell:not([disabled])",
        ".mat-mdc-calendar-body .mat-calendar-body-cell:not(.mat-calendar-body-disabled)",
        "td[role='gridcell'] button:not([disabled])",
    ]
    seen = set(); locs = []
    for sel in selectors:
        qs = page.locator(sel)
        c = qs.count()
        for i in range(min(c, 60)):
            el = qs.nth(i)
            try:
                if not el.is_visible(): continue
                box = el.bounding_box()
                if not box: continue
                key = (round(box["x"],1), round(box["y"],1), round(box["width"],1), round(box["height"],1))
                if key in seen: continue
                seen.add(key); locs.append(el)
            except Exception: continue
    return locs

def _collect_time_elements(page):
    nets = [
        "button, a, [role='button'], .slotbtn, .mat-chip, .mat-mdc-chip, .chip, .hour, [data-time], [data-slot], .times *, .time-slot *",
        "*",
    ]
    seen=set(); out=[]
    for net in nets:
        for el in page.query_selector_all(net):
            try:
                txt = (el.inner_text() or "").strip()
                if not txt: continue
                m = TIME_RX.search(txt)
                if not m: continue
                mins = _parse_time_to_minutes(txt)
                if mins is None: continue
                if not el.is_visible(): continue
                clickable = el
                for _ in range(3):
                    tag = (clickable.evaluate("n=>n.tagName") or "").lower()
                    role = clickable.get_attribute("role") or ""
                    tabindex = clickable.get_attribute("tabindex")
                    if tag in ("button","a") or role=="button" or (tabindex and int(tabindex)>=0) or clickable.get_attribute("onclick") is not None:
                        break
                    parent = clickable.evaluate_handle("n=>n.parentElement")
                    if not parent: break
                    clickable = parent
                box = el.bounding_box()
                if not box: continue
                key = (mins, round(box["x"],1), round(box["y"],1))
                if key in seen: continue
                seen.add(key)
                out.append({"el": el, "clickable": clickable, "minutes": mins})
            except Exception: continue
        if out: break
    out.sort(key=lambda d: d["minutes"])
    return out

def find_and_pick_earliest_slot(page):
    # If hours already visible, click earliest
    if _wait_for_any_slot(page, timeout_s=2.0):
        time_candidates = _collect_time_elements(page)
        if time_candidates and _click_like_human(page, time_candidates[0]["clickable"]):
            save(page, "after_click_hour_preselected_day")
            return True

    # Otherwise scan days (as before)
    for month in range(MAX_MONTHS_TO_SCAN):
        try: page.wait_for_selector(".daysgrid, .mat-calendar, .mat-mdc-calendar-body, [role='grid']", timeout=8000)
        except Exception: pass

        days = _candidate_days(page)
        if not days:
            if not _goto_next_month(page): break
            continue

        for i, d in enumerate(days[:62]):
            try:
                if not d.is_visible(): d.scroll_into_view_if_needed()
                d.click()
            except Exception:
                continue

            save(page, f"after_click_day_{month}_{i}")

            if not _wait_for_any_slot(page, timeout_s=7):
                continue

            time_candidates = _collect_time_elements(page)
            for cand in time_candidates[:15]:
                if _click_like_human(page, cand["clickable"]):
                    save(page, f"after_click_hour_{month}_{i}_{cand['minutes']}")
                    return True

        if not _goto_next_month(page): break

    return False

def _goto_next_month(root):
    for sel in (".monthnav .btn:has-text('›')",
                ".monthnav button:has-text('›')",
                "button[aria-label*='Siguiente' i]",
                "button:has-text('Siguiente')",
                "button:has-text('›')",
                "button[aria-label*='Next' i]"):
        b = root.locator(sel).first
        if b.count():
            try:
                if b.is_enabled():
                    b.click(); return True
            except Exception: continue
    return False

# ==========
# Step 4 (consent + submit) — ROBUST
# ==========
CONSENT_RXS = [
    re.compile(r"Estoy\s+informado/?a\s+sobre\s+el\s+tratamiento\s+de\s+mis\s+datos\s+personales", re.I),
    re.compile(r"tratamiento.*datos.*personales", re.I),
    re.compile(r"he\s+le[ií]do.*protecci[oó]n\s+de\s+datos", re.I),
    re.compile(r"consiento.*datos", re.I),
]

def _is_checked(node):
    try:
        return node.evaluate("""
        (el) => {
          const input = el.matches('input[type="checkbox"]') ? el
                        : el.querySelector('input[type="checkbox"], .mdc-checkbox__native-control');
          if (input) return !!input.checked;

          const aria = (el.getAttribute('aria-checked') || '').toLowerCase();
          const cls  = el.getAttribute('class') || '';
          if (aria === 'true') return true;
          if (/(^|\\s)mat-checkbox-checked(\\s|$)/.test(cls)) return true;
          if (/(^|\\s)mdc-checkbox--selected(\\s|$)/.test(cls)) return true;
          if (/(^|\\s)mdc-checkbox--checked(\\s|$)/.test(cls)) return true;
          return false;
        }
        """)
    except Exception:
        return False

def _dump_checkboxes(page):
    Path("artifacts").mkdir(exist_ok=True)
    lines = []
    try:
        cbs = page.locator("input[type='checkbox']:visible, .mat-mdc-checkbox:visible, [role='checkbox']:visible")
        n = cbs.count()
        lines.append(f"Found {n} visible checkbox-like nodes")
        for i in range(min(n, 25)):
            el = cbs.nth(i)
            try:
                txt = (el.inner_text() or "").strip()
            except Exception:
                txt = ""
            try:
                aria = el.get_attribute("aria-label") or ""
                ident = (el.get_attribute("id") or "") + " " + (el.get_attribute("class") or "")
                near = el.evaluate("""(e)=>{
                    const lab = e.closest('label') || e.parentElement;
                    const t = (lab && lab.innerText)||'';
                    return t && t.trim().slice(0,160);
                }""") or ""
                checked = "✓" if _is_checked(el) else "·"
                lines.append(f"[{i}] checked={checked} id/class={ident.strip()} aria-label={aria!r} nodeText={txt[:80]!r} nearText={near!r}")
            except Exception:
                continue
    except Exception as e:
        lines.append(f"error during dump: {e!r}")
    try:
        with open("artifacts/consent_debug.txt","w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print("\n".join(lines))
    except Exception:
        pass

def _focus_and_space(page, el):
    try: el.scroll_into_view_if_needed()
    except Exception: pass
    try: el.focus()
    except Exception: pass
    try:
        page.keyboard.press("Space")
        page.wait_for_timeout(120)
    except Exception: pass

def check_consent_by_text(page):
    save(page, "before_consent_attempt")
    _dump_checkboxes(page)

    # 1) label[for]
    try:
        lab = page.locator("label").filter(has_text=re.compile(r"informad[o/a].*tratamiento.*datos", re.I)).first
        if lab.count():
            cb_id = lab.get_attribute("for")
            if cb_id:
                input_el = page.locator(f"#{cb_id}")
                if input_el.count():
                    _focus_and_space(page, input_el.first)
                    if _is_checked(input_el.first):
                        save(page, "after_consent_label_for_space"); return True
                    try: input_el.first.click()
                    except Exception: pass
                    if _is_checked(input_el.first):
                        save(page, "after_consent_label_for_click"); return True
                    page.evaluate("""
                    (input) => {
                      const fire = (t)=> input.dispatchEvent(new Event(t,{bubbles:true,cancelable:true}));
                      if (!input.checked) input.checked = true;
                      input.setAttribute('aria-checked','true');
                      fire('input'); fire('change');
                      input.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,composed:true}));
                      const wrap = input.closest('.mat-checkbox, .mat-mdc-checkbox');
                      if (wrap) { wrap.classList.add('mat-checkbox-checked','mdc-checkbox--selected','mdc-checkbox--checked'); wrap.setAttribute('aria-checked','true'); }
                    }
                    """, input_el.first)
                    page.wait_for_timeout(150)
                    if _is_checked(input_el.first):
                        save(page, "after_consent_label_for_forced"); return True
    except Exception:
        pass

    # 2) role=checkbox
    try:
        acc = page.get_by_role("checkbox", name=re.compile(r"informad[o/a].*tratamiento.*datos", re.I))
        if acc.count():
            _focus_and_space(page, acc.first)
            if _is_checked(acc.first):
                save(page, "after_consent_role_space"); return True
            try: acc.first.click(timeout=1500)
            except Exception: pass
            if _is_checked(acc.first):
                save(page, "after_consent_role_click"); return True
    except Exception:
        pass

    # 3) by nearby container
    container = None
    for rx in CONSENT_RXS:
        try:
            block = page.locator("*").filter(has_text=rx).first
            if block.count(): container = block; break
        except Exception:
            continue

    candidates = []
    if container and container.count():
        try: container.scroll_into_view_if_needed()
        except Exception: pass
        for sel in [
            "input[type='checkbox']",
            ".mdc-checkbox__native-control",
            ".mat-mdc-checkbox input[type='checkbox']",
            ".mat-checkbox input[type='checkbox']",
            ".mat-mdc-checkbox",
            ".mat-checkbox",
            "[role='checkbox']",
        ]:
            try:
                loc = container.locator(sel)
                if loc.count(): candidates.append(loc.first)
            except Exception:
                pass
        if not candidates:
            try:
                up = container.locator("xpath=ancestor-or-self::*[position()<=4]")
                for j in range(min(4, up.count())):
                    anc = up.nth(j)
                    loc = anc.locator("input[type='checkbox'], .mdc-checkbox__native-control, .mat-mdc-checkbox, .mat-checkbox, [role='checkbox']")
                    if loc.count(): candidates.append(loc.first); break
            except Exception: pass

    if not candidates:
        try:
            vis = page.locator("input[type='checkbox']:visible, .mdc-checkbox__native-control:visible")
            if vis.count() == 1: candidates.append(vis.first)
        except Exception: pass

    for cand in candidates:
        try:
            _focus_and_space(page, cand)
            if _is_checked(cand):
                save(page, "after_consent_space_container"); return True
            try: cand.click(timeout=1200)
            except Exception: pass
            if _is_checked(cand):
                save(page, "after_consent_click_container"); return True
            page.evaluate("""
            (el) => {
              const input = el.matches('input') ? el : el.querySelector('input[type="checkbox"], .mdc-checkbox__native-control');
              const tgt = input || el;
              const fire = (t)=> tgt.dispatchEvent(new Event(t,{bubbles:true,cancelable:true}));
              const click = ()=> tgt.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,composed:true}));
              if (input && !input.checked) input.checked = true;
              if (!tgt.getAttribute('aria-checked')) tgt.setAttribute('aria-checked','true');
              fire('input'); fire('change'); click();
              const wrap = tgt.closest('.mat-checkbox, .mat-mdc-checkbox');
              if (wrap) { wrap.classList.add('mat-checkbox-checked','mdc-checkbox--selected','mdc-checkbox--checked'); wrap.setAttribute('aria-checked','true'); }
            }
            """, cand)
            page.wait_for_timeout(150)
            if _is_checked(cand):
                save(page, "after_consent_forced_container"); return True
        except Exception:
            continue

    save(page, "consent_click_failed")
    return False

# ---------- dialog + submit helpers ----------
def _try_click(page, locator, name_for_log, timeout=1500, force=False):
    try:
        if locator and locator.count():
            el = locator.first
            try: el.scroll_into_view_if_needed()
            except Exception: pass
            try:
                el.click(timeout=timeout, force=force)
                return True
            except Exception:
                try:
                    page.evaluate("(el)=>el && el.click && el.click()", el)
                    return True
                except Exception:
                    try:
                        box = el.bounding_box()
                        if box:
                            page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                            return True
                    except Exception:
                        pass
    except Exception:
        pass
    return False

def _click_topmost_confirm_button(page, labels=("CONFIRMAR","ACEPTAR","Aceptar")):
    """
    Find ALL visible confirm-like buttons anywhere, pick the one with highest z-index,
    and click it (robustly). Logs candidates to artifacts/confirm_candidates.txt
    """
    Path("artifacts").mkdir(exist_ok=True)
    try:
        candidates = page.evaluate(f"""
        (labels) => {{
          function visible(el){{
            const r = el.getBoundingClientRect();
            const cs = getComputedStyle(el);
            return !!(r.width && r.height) && cs.visibility!=='hidden' && cs.display!=='none';
          }}
          function z(el){{
            let zi = 0, n = el;
            while(n){{
              const z = parseInt(getComputedStyle(n).zIndex || '0', 10);
              if(!isNaN(z)) zi = Math.max(zi, z);
              n = n.parentElement;
            }}
            return zi;
          }}
          const qs = Array.from(document.querySelectorAll('button,[role=\"button\"],a[role=\"button\"],.mdc-button,.mat-button,.mat-raised-button'));
          const labs = labels.map(l=>l.toUpperCase());
          const out = [];
          for(const el of qs){{
            const t = (el.innerText||el.textContent||'').trim().toUpperCase();
            if(!t) continue;
            if(!labs.some(l=>t.includes(l))) continue;
            if(!visible(el)) continue;
            const r = el.getBoundingClientRect();
            out.push({{
              text: t, z: z(el), x: r.x, y: r.y, w: r.width, h: r.height,
              xpath: (function g(n){{if(!n||!n.parentElement) return '/'+n.tagName; return g(n.parentElement)+'/'+n.tagName+'['+(1+[...n.parentElement.children].indexOf(n))+']';}})(el)
            }});
          }}
          out.sort((a,b)=> b.z - a.z || a.y - b.y); // highest z, then top-most
          return out;
        }}
        """, list(labels))

        with open("artifacts/confirm_candidates.txt","w",encoding="utf-8") as f:
            for i,c in enumerate(candidates[:20]):
                f.write(f"[{i}] z={c['z']} y={round(c['y'],1)} text={c['text']}\n")

        if not candidates:
            return False

        # Try the best one
        top = candidates[0]
        # Try clicking by screen coords (most reliable for overlays)
        page.mouse.click(top["x"] + top["w"]/2, top["y"] + top["h"]/2)
        page.wait_for_timeout(300)

        # If something still blocks, try a DOM-based click using a fresh locator search
        rx = re.compile(r"(CONFIRMAR|ACEPTAR)", re.I)
        loc = page.locator("button, [role='button'], a[role='button'], .mdc-button, .mat-button").filter(has_text=rx).first
        _try_click(page, loc, "confirm_dom_click", timeout=1500, force=True)
        page.wait_for_timeout(300)
        return True
    except Exception:
        return False

def _handle_data_change_dialog(page, max_rounds=6):
    """
    Generic handler: try common dialog containers, but also fall back to 'click topmost CONFIRMAR'.
    """
    rx_dialog = re.compile(r"(Confirmaci[oó]n\s+cambio\s+de\s+datos|Los\s+siguientes\s+datos\s+han\s+cambiado)", re.I)
    rx_confirm = re.compile(r"(CONFIRMAR|ACEPTAR)", re.I)

    # small wait for overlay to mount
    page.wait_for_timeout(250)

    for r in range(max_rounds):
        save(page, f"dialog_pass_{r}")

        # 0) Make sure backdrop won't intercept pointer events
        try:
            page.evaluate("""() => {
              document.querySelectorAll('.cdk-overlay-backdrop, .modal-backdrop')
                .forEach(b => b.style.pointerEvents = 'none');
            }""")
        except Exception:
            pass

        # 1) Known dialog containers
        dialog = page.locator(
            ".cdk-overlay-container .cdk-overlay-pane [role='dialog'], "
            ".cdk-overlay-container .cdk-overlay-pane, "
            ".mat-dialog-container, .mdc-dialog__surface, .modal-dialog, [role='dialog']"
        ).filter(has_text=rx_dialog).first

        if dialog.count() and dialog.is_visible():
            # try confirm inside
            btn = dialog.get_by_role("button", name=rx_confirm).first
            if not btn.count():
                btn = dialog.locator("button, [role='button'], .mdc-button, .mat-button").filter(has_text=rx_confirm).first
            if _try_click(page, btn, "dialog_confirm", timeout=1800) or _try_click(page, btn, "dialog_confirm_force", timeout=1800, force=True):
                page.wait_for_timeout(350)
                if not dialog.is_visible(): return True

        # 2) If that failed (or dialog not matched), click topmost confirm-like button anywhere
        if _click_topmost_confirm_button(page):
            page.wait_for_timeout(400)
            # if any dialog disappeared, consider it done
            any_dialog = page.locator("[role='dialog'], .mat-dialog-container, .mdc-dialog__surface, .modal-dialog")
            if not any_dialog.count() or not any_dialog.first.is_visible():
                return True

        # 3) Keyboard fallback (focus last overlay pane and press Enter)
        try:
            overlay = page.locator(".cdk-overlay-container .cdk-overlay-pane:visible").last
            if overlay.count():
                overlay.focus()
                page.keyboard.press("Enter")
                page.wait_for_timeout(300)
                if not overlay.is_visible():
                    return True
        except Exception:
            pass

        page.wait_for_timeout(250)

    save(page, "dialog_confirm_failed")
    return False

def _wait_for_booking_result(page, timeout_s=15):
    success_rx = re.compile(
        r"(reserva\s+confirmada|cita\s+confirmada|hemos\s+enviado\s+una\s+confirmaci[oó]n|reserva\s+realizada)",
        re.I,
    )
    error_sel = ".mat-error, [role='alert'], [aria-live='polite'], .error, .mat-snack-bar-container"

    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            body_text = (page.inner_text("body") or "").strip()
            if success_rx.search(body_text):
                save(page, "booking_success")
                return "success"

            errs = page.locator(error_sel)
            if errs.count():
                texts = []
                for i in range(min(8, errs.count())):
                    try:
                        t = (errs.nth(i).inner_text() or "").strip()
                        if t:
                            texts.append(t)
                    except Exception:
                        pass
                if texts:
                    print("Form errors:", "; ".join(texts))
                    save(page, "booking_error_visible")
                    return "error"
        except Exception:
            pass
        page.wait_for_timeout(300)
    save(page, "booking_result_unknown")
    return "unknown"

def click_finish_button(page):
    rx = re.compile(r"(CREAR\s+CITA|Reservar(?:\s+cita)?|Finalizar|Confirmar|Aceptar)", re.I)
    btn = page.get_by_role("button", name=rx).first
    if not btn.count():
        btn = page.locator("button, [role='button'], a[role='button']").filter(has_text=rx).first

    if not btn.count():
        save(page, "submit_button_not_found")
        return False

    for _ in range(15):
        try:
            disabled_attr = btn.get_attribute("disabled")
            aria_dis = (btn.get_attribute("aria-disabled") or "").lower()
            cls = (btn.get_attribute("class") or "")
            pe = btn.evaluate("el => getComputedStyle(el).pointerEvents")
            if not disabled_attr and aria_dis != "true" and "disabled" not in cls and "mat-button-disabled" not in cls and pe != "none":
                break
        except Exception:
            pass
        page.wait_for_timeout(120)

    try:
        btn.scroll_into_view_if_needed()
    except Exception:
        pass

    if not _click_like_human(page, btn):
        try:
            page.evaluate("(el)=>{el.click && el.click()}", btn)
        except Exception:
            save(page, "submit_click_failed")
            return False

    # Log visible errors (non-fatal)
    try:
        errtxt = []
        for sel in [".mat-error", "[role='alert']", "[aria-live='polite']"]:
            loc = page.locator(sel)
            for i in range(min(6, loc.count())):
                t = (loc.nth(i).inner_text() or "").strip()
                if t: errtxt.append(t)
        if errtxt:
            print("Form errors:", "; ".join(errtxt))
    except Exception:
        pass

    return True

# ==========
# Step 4 flow
# ==========
def fill_by_label(page, rx, val):
    if not val: return
    loc = page.get_by_label(rx, exact=False)
    if loc.count():
        try: loc.first.fill(val)
        except Exception: pass

def fill_contact_and_confirm(page, c):
    # Fill fields
    fill_by_label(page, re.compile(r"^Nombre\b", re.I), c["name"])
    fill_by_label(page, re.compile(r"^Apellido", re.I), c["lastname"])
    fill_by_label(page, re.compile(r"(DNI|NIE|Pasaporte)", re.I), c["id"])
    fill_by_label(page, re.compile(r"Direcci[oó]n.*correo.*electr[oó]nico", re.I), c["email"])
    fill_by_label(page, re.compile(r"Confirmar.*correo", re.I), c["email_confirm"])
    fill_by_label(page, re.compile(r"C[oó]digo.*pa[ií]s", re.I), c["phone_cc"])
    fill_by_label(page, re.compile(r"N[uú]mero.*tel[eé]fono.*m[oó]vil", re.I), c["phone"])
    fill_by_label(page, re.compile(r"Confirmar.*(m[oó]vil|tel[eé]fono)", re.I), c["phone_confirm"])
    try:
        ta = page.get_by_label(re.compile(r"Notas", re.I))
        if ta.count(): ta.first.fill(c.get("notes",""))
    except Exception: pass

    # Consent
    if c.get("consent", False):
        ok = check_consent_by_text(page)
        if not ok:
            print("WARN: Could not check consent; attempting submit anyway.")
            save(page, "consent_not_checked")

    # Submit
    page.wait_for_timeout(300)
    if not click_finish_button(page):
        return
    save(page, "after_confirm")

    # Handle generic confirmation popup
    if _handle_data_change_dialog(page):
        save(page, "after_dialog_confirm")

    # Diagnostics: success/error
    result = _wait_for_booking_result(page, timeout_s=18)
    print("Booking result:", result)

# ==========
# Main
# ==========
def run(playwright: Playwright):
    validate_config()
    browser = playwright.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO_MS)
    ctx = {}
    if RECORD_VIDEO:
        Path("videos").mkdir(exist_ok=True)
        ctx["record_video_dir"] = "videos"
    context = browser.new_context(**ctx)

    try:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
    except Exception: pass

    page = context.new_page()
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)

    try:
        print(f"Opening {BASE_URL} ...")
        if not wait_for_app(page, BASE_URL):
            save(page, "cannot_load_app"); sys.exit(1)

        dismiss_cookies(page)

        click_first_sucursal(page); save(page, "after_step1")
        select_tramite(page, TARGET_TRAMITE); save(page, "after_step2")

        print("Selecting day/hour …")
        ok = find_and_pick_earliest_slot(page)
        save(page, "after_step3_calendar")
        if not ok:
            print("No hay citas disponibles (no slots found).")
            save(page, "no_slots_debug"); sys.exit(2)

        print("Filling contact …")
        fill_contact_and_confirm(page, CONTACT)

        print("Done.")
    finally:
        Path("artifacts").mkdir(exist_ok=True)
        try: context.tracing.stop(path="artifacts/trace.zip")
        except Exception: pass
        context.close(); browser.close()

if __name__ == "__main__":
    with sync_playwright() as p:
        run(p)