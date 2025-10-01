import os, re, sys, time
from pathlib import Path
from playwright.sync_api import Playwright, sync_playwright, expect

# ======================
# CONFIG (env-overridable)
# ======================
BASE_URL = os.getenv("BASE_URL", "https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/")
TARGET_TRAMITE = os.getenv("TARGET_TRAMITE", "Asistencia telefónica para la homologación y equivalencia de títulos universitarios extranjeros")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
SLOW_MO_MS = int(os.getenv("SLOW_MO_MS", "120"))
MAX_MONTHS_TO_SCAN = int(os.getenv("MAX_MONTHS_TO_SCAN", "2"))  # current + next by default
DEFAULT_TIMEOUT_MS = int(os.getenv("DEFAULT_TIMEOUT_MS", "20000"))
BREAK_AT = os.getenv("BREAK_AT", "")  # e.g.: "after_step1,after_step2"
RECORD_VIDEO = os.getenv("RECORD_VIDEO", "true").lower() == "true"

CONTACT = {
    # Core
    "name":           os.getenv("CONTACT_NAME",          "Monica"),
    "lastname":       os.getenv("CONTACT_LASTNAME",      "Pérez Villarroel"),
    "id":             os.getenv("CONTACT_ID",            "Z0428685Q"),
    "email":          os.getenv("CONTACT_EMAIL",         "monicaperezvillarroel060@gmail.com"),
    "email_confirm":  os.getenv("CONTACT_EMAIL_CONFIRM", "monicaperezvillarroel060@gmail.com"),
    "phone_cc":       os.getenv("CONTACT_PHONE_CC",      "+34"),
    "phone":          os.getenv("CONTACT_PHONE",         "613304514"),
    "phone_confirm":  os.getenv("CONTACT_PHONE_CONFIRM", "613304514"),
    "notes":          os.getenv("CONTACT_NOTES",         "información de expediente 2022-06976"),
    "consent":        os.getenv("CONTACT_CONSENT",       "true").lower() == "true",
}

# ==========
# Utilities
# ==========
def _rx_contains(text_fragment: str):
    frag = re.sub(r"\s+", r"\\s+", text_fragment.strip())
    return re.compile(frag, re.IGNORECASE)

def save_artifacts(page, prefix="debug"):
    Path("artifacts").mkdir(exist_ok=True)
    try:
        page.screenshot(path=f"artifacts/{prefix}.png", full_page=True)
    except Exception:
        pass

def wait_for_app(page, url, timeout_s=90):
    start = time.time(); last_err = None
    while time.time() - start < timeout_s:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            if page.content():
                return True
        except Exception as e:
            last_err = e
        time.sleep(1)
    if last_err: print(f"Failed to reach app within {timeout_s}s: {last_err}")
    return False

# ====================
# Step 1: Sucursal
# ====================
def click_first_sucursal(page):
    header_rx = re.compile(r"SELECCIONAR\s+(SUCURSAL|CENTRO|OFICINA)", re.I)
    s1_header = page.locator(".hdr, button").filter(has_text=header_rx).first
    if s1_header.count():
        try:
            expanded = s1_header.get_attribute("aria-expanded")
            if expanded is not None and expanded.lower() == "false":
                s1_header.click()
        except Exception:
            pass

    # Try radio buttons
    radios = page.locator('input[type="radio"][name="sucursal"]')
    if radios.count():
        radios.first.check(); return

    # Fallbacks
    role_radios = page.get_by_role("radio")
    if role_radios.count():
        role_radios.first.check(); return

    combo = page.get_by_role("combobox").first
    if combo.count():
        combo.click(); page.get_by_role("option").first.click(); return

    label = page.locator("label.radio-item, label").first
    if label.count():
        try: label.click()
        except Exception:
            try: label.locator("input").first.check()
            except Exception: pass
        return

    save_artifacts(page, "step1_failed")
    raise RuntimeError("Could not pick Step 1 (Sucursal/Centro). Saved artifacts/step1_failed.png")

# ====================
# Step 2: Trámite
# ====================
def select_tramite(page, tramite_text):
    target_rx = _rx_contains(tramite_text)
    step2_rx = re.compile(r"SELECCIONAR\s+TR[ÁA]MITE", re.I)

    def _impl(root):
        step2 = root.locator("section, div").filter(has_text=step2_rx).first
        if step2.count():
            try:
                expanded = step2.get_attribute("aria-expanded")
                if expanded is not None and expanded.lower() == "false":
                    hdr = step2.locator(".hdr, button, [role='button']").first
                    if hdr.count(): hdr.click()
            except Exception: pass

        # Common pattern on Qmatic pages
        radio_label = root.locator("label.radio-item, label").filter(has_text=target_rx).first
        if radio_label.count():
            try: radio_label.click()
            except Exception: radio_label.locator("input[type=radio]").first.check()
            return True

        combo = root.get_by_role("combobox").first
        if not combo.count():
            combo = root.get_by_role("button").filter(has_text=re.compile("Seleccionar\\s+Tr[áa]mite|Tr[áa]mite", re.I)).first
        if combo.count():
            combo.click()
            opt = root.get_by_role("option", name=target_rx).first
            if not opt.count():
                opt = root.locator(
                    "[role='listbox'] [role='option'], "
                    ".mat-select-panel .mat-option-text, "
                    ".cdk-overlay-pane .mat-option-text, "
                    ".cdk-overlay-pane [role='option']"
                ).filter(has_text=target_rx).first
            if opt.count():
                opt.click(); return True

        li = root.locator("li, .mat-option, [role='option']").filter(has_text=target_rx).first
        if li.count(): li.click(); return True
        return False

    if _impl(page): return
    for frame in page.frames:
        try:
            url = (frame.url or "").lower()
            if "qmatic" in url or "booking" in url:
                if _impl(frame): return
        except Exception: continue

    save_artifacts(page, "select_tramite_failed")
    raise RuntimeError("Could not select the trámite — artifacts/select_tramite_failed.png")

# ===========================
# Step 3: Calendar & slots
# ===========================
def _month_label_text(root):
    lbl = root.locator(".monthnav > div").first
    return (lbl.inner_text().strip() if lbl.count() else "")

def _goto_next_month(root):
    before = _month_label_text(root)
    next_btn = root.locator('.monthnav .btn', has_text='›').first
    if not next_btn.count() or not next_btn.is_enabled():
        next_btn = root.get_by_role("button", name=re.compile(r"Siguiente|›", re.I)).first
        if not next_btn.count() or not next_btn.is_enabled():
            return False
    next_btn.click()
    t0 = time.time()
    while time.time() - t0 < 3.0:
        after = _month_label_text(root)
        if after and after != before:
            return True
        time.sleep(0.05)
    return True

def _wait_for_slots_or_empty(root, timeout_s=4.0):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if root.locator(".slots .slotbtn, .slotbtn, [data-time], .slots [role='button']").count() > 0:
            return True
        if root.locator(".emptybox, .muted, .no-slots, text=/No hay.*disponible/i").count() > 0:
            return False
        time.sleep(0.05)
    return False

def _pick_first_slot(root):
    slot = root.locator('.slotbtn').first
    if not slot.count():
        slot = root.locator('[data-time], .slots [role="button"]').first
    if not slot.count():
        return False
    expect(slot).to_be_visible()
    slot.click()
    return True

def find_and_pick_earliest_slot(page):
    # Ensure Step 3 panel is open
    s3_header = page.locator(".hdr, button").filter(has_text=re.compile("SELECCIONAR\\s+FECHA|FECHA Y HORA", re.I)).first
    if s3_header.count():
        try:
            expanded = s3_header.get_attribute("aria-expanded")
            if expanded is not None and expanded.lower() == "false":
                s3_header.click()
        except Exception: pass

    root = page  # calendar lives in main doc on the target
    for _ in range(MAX_MONTHS_TO_SCAN):
        # Enabled days in view
        day_buttons = root.locator('.daysgrid .day:not([disabled])')
        if day_buttons.count() == 0:
            if not _goto_next_month(root):
                break
            continue

        for i in range(day_buttons.count()):
            btn = day_buttons.nth(i)
            try:
                btn.click()
            except Exception:
                continue

            if not _wait_for_slots_or_empty(root):
                continue

            if _pick_first_slot(root):
                return True

        if not _goto_next_month(root):
            break

    return False

# ====================================
# Step 4: Fill contact + confirm
# ====================================
def fill_by_label_or_placeholder(page, label_rx, value):
    if value is None or value == "": return False
    # Try "get_by_label" first (robust with aria/for associations)
    ctl = page.get_by_label(label_rx, exact=False)
    if ctl.count():
        try: ctl.first.fill(value); return True
        except Exception: pass
    # Try placeholder fallback
    ph = page.locator(f'input[placeholder*="{value[:4]}" i], textarea[placeholder*="{value[:4]}" i]').first
    if ph.count():
        try: ph.fill(value); return True
        except Exception: pass
    return False

# ==========================================
# Step 4.5: Click final "Aceptar / Coger cita"
# ==========================================
def _is_enabled(loc):
    try:
        if not loc.count(): return False
        if loc.first.is_visible() and loc.first.is_enabled():
            # Consider attributes that sometimes gate clicks
            disabled_attr = loc.first.get_attribute("disabled")
            aria_disabled = (loc.first.get_attribute("aria-disabled") or "").lower()
            if disabled_attr is not None and disabled_attr not in ("", "false"):
                return False
            if aria_disabled in ("true", "1"):
                return False
            return True
    except Exception:
        pass
    return False

def click_finish_button(page, timeout_ms=10000):
    """
    Clicks the final button to complete the booking. Handles variants:
    'Aceptar', 'ACEPTAR', 'Coger cita', 'Reservar', 'Finalizar', 'Confirmar', etc.
    Also searches inside iframes just in case.
    """
    labels_rx = re.compile(
        r"(?:^|\b)(Aceptar|ACEPTAR|Coger\s+cita|CREAR\s+CITA|Reservar(?:\s+cita)?|Finalizar|Confirmar)(?:\b|$)",
        re.I
    )

    def _find_and_click(root):
        # 1) Role=button by accessible name
        btn = root.get_by_role("button", name=labels_rx).first
        if not _is_enabled(btn):
            # 2) Visible text match on <button> or <a role=button>
            btn = root.locator("button, [role='button']").filter(has_text=labels_rx).first

        if not _is_enabled(btn):
            # 3) Submit inputs (by text or any submit if only one)
            cand = root.locator("input[type=submit], button[type=submit]").filter(has_text=labels_rx).first
            btn = cand if cand.count() else root.locator("input[type=submit], button[type=submit]").first

        if not btn.count():
            return False

        try:
            expect(btn).to_be_visible(timeout=timeout_ms)
        except Exception:
            try: btn.scroll_into_view_if_needed()
            except Exception: pass

        # Wait briefly for dynamic enablement
        t0 = time.time()
        while time.time() - t0 < timeout_ms / 1000.0:
            if _is_enabled(btn):
                break
            time.sleep(0.05)

        # Try normal click; fall back to JS click
        try:
            btn.click()
        except Exception:
            try:
                root.evaluate("(el)=>el.click()", btn)
            except Exception:
                return False

        return True

    # Try main page first
    if _find_and_click(page):
        return True

    # Try frames next
    for fr in page.frames:
        try:
            if _find_and_click(fr):
                return True
        except Exception:
            continue

    # Very broad last chance
    try:
        any_btn = page.locator("button, [role='button'], input[type=submit]").filter(has_text=labels_rx).first
        if _is_enabled(any_btn):
            any_btn.click(); return True
    except Exception:
        pass

    save_artifacts(page, "finish_button_not_found")
    return False

def fill_contact_and_confirm(page, contact):
    def _fill(selector, value):
        if value is None or value == "": return False
        loc = page.locator(selector)
        if loc.count():
            loc.first.fill(value); return True
        return False

    # Known IDs used by our mock as a fast path (won't hurt on real page—locators just won't exist)
    _fill("#input_name",            contact["name"])
    _fill("#input_lastname",        contact["lastname"])
    _fill("#input_id",              contact["id"])
    _fill("#input_email",           contact["email"])
    _fill("#input_email_confirm",   contact.get("email_confirm") or contact["email"])
    _fill("#input_phone_cc",        contact["phone_cc"])
    _fill("#input_phone",           contact["phone"])
    _fill("#input_phone_confirm",   contact.get("phone_confirm") or contact["phone"])
    _fill("#input_notes",           contact.get("notes", ""))

    # Real page — fill by visible labels (case-insensitive, accents tolerated)
    fill_by_label_or_placeholder(page, re.compile(r"^Nombre\b", re.I),                          contact["name"])
    fill_by_label_or_placeholder(page, re.compile(r"^Apellido", re.I),                          contact["lastname"])
    fill_by_label_or_placeholder(page, re.compile(r"(DNI|NIE|Pasaporte)", re.I),                contact["id"])
    fill_by_label_or_placeholder(page, re.compile(r"Direcci[oó]n.*correo.*electr[oó]nico", re.I), contact["email"])
    fill_by_label_or_placeholder(page, re.compile(r"Confirmar.*correo", re.I),                  contact.get("email_confirm") or contact["email"])
    fill_by_label_or_placeholder(page, re.compile(r"C[oó]digo.*pa[ií]s", re.I),                 contact["phone_cc"])
    fill_by_label_or_placeholder(page, re.compile(r"N[uú]mero.*tel[eé]fono.*m[oó]vil", re.I),   contact["phone"])
    fill_by_label_or_placeholder(page, re.compile(r"Confirmar.*(m[oó]vil|tel[eé]fono)", re.I),  contact.get("phone_confirm") or contact["phone"])
    # Notes may be a textarea
    try:
        ta = page.get_by_label(re.compile(r"Notas", re.I))
        if ta.count(): ta.first.fill(contact.get("notes", ""))
    except Exception:
        pass

    # Consent checkbox
    if contact.get("consent", False):
        consent = page.get_by_label(re.compile(r"tratamiento.*datos.*personales|consiento|he le[ií]do", re.I))
        if consent.count():
            try: consent.first.check()
            except Exception:
                try: consent.first.click()
                except Exception: pass
        else:
            # Try id used in mock
            try: page.locator("#input_consent").check()
            except Exception: pass

    # Generic confirm/continue if present
    confirm_rx = re.compile(r"Confirmar|Continuar|Siguiente|Finalizar|Reservar", re.I)
    confirm_btn = page.locator(".btn.primary", has_text=confirm_rx).first
    if not confirm_btn.count():
        confirm_btn = page.get_by_role("button", name=confirm_rx).first
    if confirm_btn.count():
        try:
            expect(confirm_btn).to_be_visible()
            confirm_btn.click()
            time.sleep(1.0)
        except Exception:
            pass  # We'll rely on the explicit finish click below

    # NEW: explicit finish for 'Aceptar' / 'Coger cita' (or if generic was absent/ineffective)
    if not click_finish_button(page):
        # One more attempt with very specific selectors commonly seen on the site
        try:
            b = page.locator("#btnAceptar, button:has-text('ACEPTAR'), button:has-text('Aceptar'), button:has-text('Coger cita')")
            if b.count():
                b.first.click()
            else:
                raise RuntimeError("No final button to click")
        except Exception:
            save_artifacts(page, "final_click_failed")
            raise RuntimeError("Could not find/click the final 'Aceptar / Coger cita' button — see artifacts/final_click_failed.png")

    time.sleep(2)
    save_artifacts(page, "after_confirm")

# ==========
# Main flow
# ==========
def run(playwright: Playwright):
    browser = playwright.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO_MS)
    context_kwargs = {}
    if RECORD_VIDEO:
        Path("videos").mkdir(exist_ok=True)
        context_kwargs["record_video_dir"] = "videos"
    context = browser.new_context(**context_kwargs)

    # Console & network logs
    def on_console(msg): print("[console]", msg.type, msg.text)
    def on_request(req): print(">>", req.method, req.url)
    def on_response(res): print("<<", res.status, res.url)
    context.on("request", on_request)
    context.on("response", on_response)

    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    page.on("console", on_console)
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)

    print(f"Opening {BASE_URL} ...")
    if not wait_for_app(page, BASE_URL, timeout_s=90):
        save_artifacts(page, "cannot_load_app")
        context.tracing.stop(path="artifacts/trace.zip")
        context.close(); browser.close()
        sys.exit(1)

    # Cookie banner best-effort
    for sel in ("#acceptCookies", "text=Aceptar", "button:has-text('Aceptar')", "button:has-text('ACEPTAR')"):
        try:
            btn = page.locator(sel)
            if btn.count():
                btn.first.click(); break
        except Exception: pass

    # Step 1
    click_first_sucursal(page)
    if "after_step1" in BREAK_AT: page.pause()
    save_artifacts(page, "after_step1")

    # Step 2
    select_tramite(page, TARGET_TRAMITE)
    if "after_step2" in BREAK_AT: page.pause()
    save_artifacts(page, "after_step2")

    # Step 3
    print("Searching for the earliest available day & time (current + next month) ...")
    has_slot = find_and_pick_earliest_slot(page)
    save_artifacts(page, "after_step3_calendar")
    if "after_step3" in BREAK_AT: page.pause()
    if not has_slot:
        print("No hay citas disponibles (no slots found).")
        save_artifacts(page, "no_slots_found")
        context.tracing.stop(path="artifacts/trace.zip")
        context.close(); browser.close()
        sys.exit(2)

    # Step 4
    print("Filling contact details and confirming ...")
    fill_contact_and_confirm(page, CONTACT)
    if "after_confirm" in BREAK_AT: page.pause()

    context.tracing.stop(path="artifacts/trace.zip")
    context.close()
    browser.close()
    print("Trace saved to artifacts/trace.zip (view: playwright show-trace artifacts/trace.zip)")

if __name__ == "__main__":
    with sync_playwright() as p:
        run(p)
