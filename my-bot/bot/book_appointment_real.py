import os, re, sys, time
from pathlib import Path
from playwright.sync_api import Playwright, sync_playwright, expect

# ======================
# CONFIG (env-overridable)
# ======================
BASE_URL = os.getenv("BASE_URL", "https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/")
TARGET_TRAMITE = os.getenv("TARGET_TRAMITE", "Asistencia telefónica para la homologación y equivalencia de títulos universitarios extranjeros")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
SLOW_MO_MS = int(os.getenv("SLOW_MO_MS", "150"))
MAX_MONTHS_TO_SCAN = int(os.getenv("MAX_MONTHS_TO_SCAN", "6"))
DEFAULT_TIMEOUT_MS = int(os.getenv("DEFAULT_TIMEOUT_MS", "20000"))
BREAK_AT = os.getenv("BREAK_AT", "")  # e.g.: "after_step1,after_step2"
RECORD_VIDEO = os.getenv("RECORD_VIDEO", "true").lower() == "true"

CONTACT = {
    "name":  os.getenv("CONTACT_NAME",  "Ada Lovelace"),
    "id":    os.getenv("CONTACT_ID",    "12345678X"),
    "email": os.getenv("CONTACT_EMAIL", "ada@example.com"),
    "phone": os.getenv("CONTACT_PHONE", "600600600"),
}

def _rx_contains(text_fragment: str):
    frag = re.sub(r"\s+", r"\\s+", text_fragment.strip())
    return re.compile(frag, re.IGNORECASE)

def save_artifacts(page, prefix="debug"):
    Path("artifacts").mkdir(exist_ok=True)
    page.screenshot(path=f"artifacts/{prefix}.png", full_page=True)

def wait_for_app(page, url, timeout_s=60):
    start = time.time(); last_err = None
    while time.time() - start < timeout_s:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            if page.content():
                return True
        except Exception as e:
            last_err = e
        time.sleep(1)
    if last_err: print(f"Failed to reach app within {timeout_s}s: {last_err}")
    return False

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
    radios = page.locator('input[type="radio"][name="sucursal"]')
    if radios.count():
        radios.first.check(); return
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
    for frame in page.frames:
        try:
            if _impl(frame): return
        except Exception: continue
    save_artifacts(page, "select_tramite_failed")
    raise RuntimeError("Could not select the trámite — saved artifacts/select_tramite_failed.png")

def find_and_pick_earliest_slot(page):
    s3_header = page.locator(".hdr, button").filter(has_text=re.compile("SELECCIONAR\\s+FECHA|FECHA Y HORA", re.I)).first
    if s3_header.count():
        try:
            expanded = s3_header.get_attribute("aria-expanded")
            if expanded is not None and expanded.lower() == "false":
                s3_header.click()
        except Exception: pass
    for _ in range(MAX_MONTHS_TO_SCAN):
        day_buttons = page.locator('.daysgrid .day:not([disabled])')
        day_count = day_buttons.count()
        if day_count == 0:
            # CORRECTED: use name=regex rather than filter(has=regex)
            day_buttons = page.get_by_role("button", name=re.compile(r"^\s*\d{1,2}\s*$"))
            day_count = day_buttons.count()
        for i in range(day_count):
            day = day_buttons.nth(i)
            try: day.click()
            except Exception: continue
            found_slots = False
            for _ in range(40):
                if page.locator('.slotbtn, [data-time], .slots [role="button"]').count() > 0:
                    found_slots = True; break
                if page.locator('.muted, .emptybox, .no-slots, text=/No hay.*disponible/i').count() > 0:
                    break
                time.sleep(0.15)
            if not found_slots: continue
            slot = page.locator('.slotbtn').first
            if slot.count() == 0:
                slot = page.locator('[data-time], .slots [role="button"]').first
            expect(slot).to_be_visible()
            slot.click()
            return True
        next_btn = page.locator('.monthnav .btn', has_text='›')
        if not next_btn.count():
            next_btn = page.get_by_role("button", name=re.compile(r"Siguiente|›", re.I)).first
        if next_btn.count() and next_btn.is_enabled():
            next_btn.click(); continue
        break
    return False

def fill_contact_and_confirm(page, contact):
    def _fill(selector, value):
        if page.locator(selector).count():
            page.fill(selector, value); return True
        return False
    ok = 0
    ok += _fill("#input_name",  contact["name"])
    ok += _fill("#input_id",    contact["id"])
    ok += _fill("#input_email", contact["email"])
    ok += _fill("#input_phone", contact["phone"])
    if ok == 0:
        def fill_by_label(label_rx, value):
            label = page.get_by_label(label_rx, exact=False)
            if label.count(): label.first.fill(value); return True
            return False
        filled_any = False
        filled_any |= fill_by_label(re.compile(r"Nombre|Name", re.I), contact["name"])
        filled_any |= fill_by_label(re.compile(r"DNI|Identificaci[oó]n|ID", re.I), contact["id"])
        filled_any |= fill_by_label(re.compile(r"Correo|Email|E-?mail", re.I), contact["email"])
        filled_any |= fill_by_label(re.compile(r"Tel[eé]fono|Phone", re.I), contact["phone"])
        if not filled_any:
            print("Warning: could not auto-fill contact fields; adjust selectors for the real site.")
    confirm_btn = page.locator(".btn.primary", has_text=re.compile("Confirmar|Continuar|Siguiente|Finalizar|Reservar", re.I)).first
    if not confirm_btn.count():
        confirm_btn = page.get_by_role("button", name=re.compile("Confirmar|Continuar|Siguiente|Finalizar|Reservar", re.I)).first
    expect(confirm_btn).to_be_visible()
    confirm_btn.click()
    time.sleep(2)
    save_artifacts(page, "after_confirm")

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

    click_first_sucursal(page)
    if "after_step1" in BREAK_AT: page.pause()
    save_artifacts(page, "after_step1")

    select_tramite(page, TARGET_TRAMITE)
    if "after_step2" in BREAK_AT: page.pause()
    save_artifacts(page, "after_step2")

    print("Searching for the earliest available day & time ...")
    has_slot = find_and_pick_earliest_slot(page)
    save_artifacts(page, "after_step3_calendar")
    if "after_step3" in BREAK_AT: page.pause()
    if not has_slot:
        print("No hay citas disponibles (no slots found).")
        save_artifacts(page, "no_slots_found")
        context.tracing.stop(path="artifacts/trace.zip")
        context.close(); browser.close()
        sys.exit(2)

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
