import os
import re
import sys
import time
from pathlib import Path
from playwright.sync_api import Playwright, sync_playwright, expect

# ======================
# CONFIG (env-overridable)
# ======================
BASE_URL = os.getenv("BASE_URL", "https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/")
TARGET_TRAMITE = os.getenv(
    "TARGET_TRAMITE",
    "Asistencia telefónica para la homologación y equivalencia de títulos universitarios extranjeros",
)
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"  # default to headed for debug
SLOW_MO_MS = int(os.getenv("SLOW_MO_MS", "150"))            # helps with dynamic UIs
MAX_MONTHS_TO_SCAN = int(os.getenv("MAX_MONTHS_TO_SCAN", "6"))

CONTACT = {
    "name":  os.getenv("CONTACT_NAME",  "Monica Pérez Villarroel"),
    "id":    os.getenv("CONTACT_ID",    "Z0428685Q"),
    "email": os.getenv("CONTACT_EMAIL", "monicaperezvillarroel060@gmail.com"),
    "phone": os.getenv("CONTACT_PHONE", "613304514"),
}

# ======================
# UTILITIES
# ======================
def _rx_contains(text_fragment: str):
    """Return a case-insensitive regex that tolerates extra whitespace (keeps accents)."""
    frag = re.sub(r"\s+", r"\\s+", text_fragment.strip())
    return re.compile(frag, re.IGNORECASE)

def save_artifacts(page, prefix="debug"):
    Path("artifacts").mkdir(exist_ok=True)
    page.screenshot(path=f"artifacts/{prefix}.png", full_page=True)

def wait_for_app(page, url, timeout_s=60):
    """Try to open the app root; don't assume specific markup."""
    start = time.time()
    last_err = None
    while time.time() - start < timeout_s:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            # Any visible content is fine; real site builds quickly after DOMContentLoaded
            if page.content():
                return True
        except Exception as e:
            last_err = e
        time.sleep(1)
    if last_err:
        print(f"Failed to reach app within {timeout_s}s: {last_err}")
    return False

# ======================
# STEP 1: SUCURSAL / CENTRO
# ======================
def click_first_sucursal(page):
    """
    On real Qmatic builds, Step 1 may be radios or a dropdown/combobox, sometimes in Spanish variants.
    This tries several patterns to pick the first available option and unlock Step 2.
    """
    header_rx = re.compile(r"SELECCIONAR\s+(SUCURSAL|CENTRO|OFICINA)", re.I)

    # If there is a clear step header, try expanding it
    s1_header = page.locator(".hdr, button").filter(has_text=header_rx).first
    if s1_header.count():
        try:
            # If aria-expanded exists and is false, click to open
            expanded = s1_header.get_attribute("aria-expanded")
            if expanded is not None and expanded.lower() == "false":
                s1_header.click()
        except Exception:
            pass  # not fatal

    # A) radios named 'sucursal'
    radios = page.locator('input[type="radio"][name="sucursal"]')
    if radios.count():
        radios.first.check()
        return

    # B) any radio by role
    role_radios = page.get_by_role("radio")
    if role_radios.count():
        role_radios.first.check()
        return

    # C) combobox: open + choose first option
    combo = page.get_by_role("combobox").first
    if combo.count():
        combo.click()
        # pick first enabled option
        opts = page.get_by_role("option")
        expect(opts).to_have_count(lambda c: c >= 1)
        opts.first.click()
        return

    # D) fallback: first label that looks like option
    label = page.locator("label.radio-item, label").first
    if label.count():
        try:
            label.click()
        except Exception:
            try:
                label.locator("input").first.check()
            except Exception:
                pass
        return

    save_artifacts(page, "step1_failed")
    raise RuntimeError("Could not pick Step 1 (Sucursal/Centro). Saved artifacts/step1_failed.png")

# ======================
# STEP 2: TRÁMITE
# ======================
def select_tramite(page, tramite_text):
    """
    Robustly select the target service in Step 2 on the real site.
    Tries multiple UI patterns: radio list, combobox/dropdown (Material), generic options,
    and retries inside iframes if needed.
    """
    target_rx = _rx_contains(tramite_text)
    step2_rx = re.compile(r"SELECCIONAR\s+TR[ÁA]MITE", re.I)

    def _impl(root):
        # Ensure Step 2 panel is open if present
        step2 = root.locator("section, div").filter(has_text=step2_rx).first
        if step2.count():
            try:
                expanded = step2.get_attribute("aria-expanded")
                if expanded is not None and expanded.lower() == "false":
                    # click something that toggles it
                    hdr = step2.locator(".hdr, button, [role='button']").first
                    if hdr.count():
                        hdr.click()
            except Exception:
                pass

        # Strategy A: radio list labels
        radio_label = root.locator("label.radio-item, label").filter(has_text=target_rx).first
        if radio_label.count():
            try:
                radio_label.click()
            except Exception:
                radio_label.locator("input[type=radio]").first.check()
            return True

        # Strategy B: combobox/listbox (Material)
        combo = root.get_by_role("combobox").first
        if not combo.count():
            # button that opens the dropdown
            combo = root.get_by_role("button").filter(has_text=re.compile("Seleccionar\\s+Tr[áa]mite|Tr[áa]mite", re.I)).first
        if combo.count():
            combo.click()
            # Try role="option" first
            opt = root.get_by_role("option", name=target_rx).first
            if not opt.count():
                # fallback patterns in overlay panes
                opt = root.locator(
                    "[role='listbox'] [role='option'], "
                    ".mat-select-panel .mat-option-text, "
                    ".cdk-overlay-pane .mat-option-text, "
                    ".cdk-overlay-pane [role='option']"
                ).filter(has_text=target_rx).first
            if opt.count():
                opt.click()
                return True

        # Strategy C: generic list items (virtual scroller)
        li = root.locator("li, .mat-option, [role='option']").filter(has_text=target_rx).first
        if li.count():
            li.click()
            return True

        return False

    # Try in main page first
    if _impl(page):
        return

    # Try in iframes scoped by URL hint
    for frame in page.frames:
        try:
            url = (frame.url or "").lower()
            if "qmatic" in url or "booking" in url:
                if _impl(frame):
                    return
        except Exception:
            continue

    # Try any iframe
    for frame in page.frames:
        try:
            if _impl(frame):
                return
        except Exception:
            continue

    save_artifacts(page, "select_tramite_failed")
    raise RuntimeError("Could not select the trámite — saved artifacts/select_tramite_failed.png")

# ======================
# STEP 3: FECHA & HORA
# ======================
def find_and_pick_earliest_slot(page):
    """
    Iterate months (UI next '›' button) and days; when a day has slots, pick the first slot.
    Works with both our mock and the real site if those classes/roles exist.
    """
    # Ensure the Step 3 panel is open if the page uses a collapsible panel
    s3_header = page.locator(".hdr, button").filter(has_text=re.compile("SELECCIONAR\\s+FECHA|FECHA Y HORA", re.I)).first
    if s3_header.count():
        try:
            expanded = s3_header.get_attribute("aria-expanded")
            if expanded is not None and expanded.lower() == "false":
                s3_header.click()
        except Exception:
            pass

    for _ in range(MAX_MONTHS_TO_SCAN):
        # Click each enabled day
        day_buttons = page.locator('.daysgrid .day:not([disabled])')
        day_count = day_buttons.count()
        # If this selector doesn't exist on the real site, try a generic day button fallback
        if day_count == 0:
            day_buttons = page.get_by_role("button", name=re.compile(r"^\s*\d{1,2}\s*$"))
            day_count = day_buttons.count()

        for i in range(day_count):
            day = day_buttons.nth(i)
            try:
                day.click()
            except Exception:
                continue

            # Wait for either slots or a "no slots" marker to appear
            found_slots = False
            for _ in range(40):  # ~6s with slowMo
                if page.locator('.slotbtn, [data-time], .slots [role="button"]').count() > 0:
                    found_slots = True
                    break
                if page.locator('.muted, .emptybox, .no-slots, text=/No hay.*disponible/i').count() > 0:
                    break
                time.sleep(0.15)

            if not found_slots:
                continue

            # Pick earliest slot
            slot = page.locator('.slotbtn').first
            if slot.count() == 0:
                # more generic fallback
                slot = page.locator('[data-time], .slots [role="button"]').first
            expect(slot).to_be_visible()
            slot.click()
            return True

        # Move to next month if there is a "Siguiente" or '›' button
        next_btn = page.locator('.monthnav .btn', has_text='›')
        if not next_btn.count():
            # try a generic next control
            next_btn = page.get_by_role("button", name=re.compile(r"Siguiente|›", re.I)).first
        if next_btn.count() and next_btn.is_enabled():
            next_btn.click()
            continue
        break

    return False

# ======================
# STEP 4: CONTACTO
# ======================
def fill_contact_and_confirm(page, contact):
    """
    Fill contact details and press the main confirmation button.
    Works for our mock; on the real site, you may need to adjust field selectors if they differ.
    """
    # If the real site uses different IDs, try fallbacks
    def _fill(selector, value):
        if page.locator(selector).count():
            page.fill(selector, value)
            return True
        return False

    # Common IDs in our mock:
    ok = 0
    ok += _fill("#input_name", contact["name"])
    ok += _fill("#input_id", contact["id"])
    ok += _fill("#input_email", contact["email"])
    ok += _fill("#input_phone", contact["phone"])

    # If none matched (real site), try more generic name/email/phone field guesses
    if ok == 0:
        # Guess by label text
        def fill_by_label(label_rx, value):
            label = page.get_by_label(label_rx, exact=False)
            if label.count():
                label.first.fill(value)
                return True
            return False

        filled_any = False
        filled_any |= fill_by_label(re.compile(r"Nombre|Name", re.I), contact["name"])
        filled_any |= fill_by_label(re.compile(r"DNI|Identificaci[oó]n|ID", re.I), contact["id"])
        filled_any |= fill_by_label(re.compile(r"Correo|Email|E-?mail", re.I), contact["email"])
        filled_any |= fill_by_label(re.compile(r"Tel[eé]fono|Phone", re.I), contact["phone"])
        if not filled_any:
            print("Warning: could not auto-fill contact fields; check selectors for the real site.")

    # Click a confirm-like button
    confirm_btn = page.locator(".btn.primary", has_text=re.compile("Confirmar|Continuar|Siguiente|Finalizar|Reservar", re.I)).first
    if not confirm_btn.count():
        confirm_btn = page.get_by_role("button", name=re.compile("Confirmar|Continuar|Siguiente|Finalizar|Reservar", re.I)).first
    expect(confirm_btn).to_be_visible()
    confirm_btn.click()

    # Not all real flows show an inline success box; we just wait a bit
    time.sleep(2)
    save_artifacts(page, "after_confirm")

# ======================
# MAIN
# ======================
def run(playwright: Playwright):
    browser = playwright.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO_MS)
    context = browser.new_context()
    # Trace is invaluable for dynamic Angular/Material apps
    context.tracing.start(screenshots=True, snapshots=True, sources=True)

    page = context.new_page()
    page.set_default_timeout(20000)  # 20s per Playwright action

    print(f"Opening {BASE_URL} ...")
    if not wait_for_app(page, BASE_URL, timeout_s=90):
        save_artifacts(page, "cannot_load_app")
        context.tracing.stop(path="artifacts/trace.zip")
        context.close(); browser.close()
        sys.exit(1)

    # Dismiss cookie bars if present (best-effort)
    for sel in ("#acceptCookies", "text=Aceptar", "button:has-text('Aceptar')", "button:has-text('ACEPTAR')"):
        try:
            btn = page.locator(sel)
            if btn.count():
                btn.first.click()
                break
        except Exception:
            pass

    # Step 1 → Step 2
    click_first_sucursal(page)
    select_tramite(page, TARGET_TRAMITE)

    # Step 3
    print("Searching for the earliest available day & time ...")
    has_slot = find_and_pick_earliest_slot(page)
    if not has_slot:
        print("No hay citas disponibles (no slots found within the scanned months).")
        save_artifacts(page, "no_slots_found")
        context.tracing.stop(path="artifacts/trace.zip")
        context.close(); browser.close()
        sys.exit(2)

    # Step 4
    print("Filling contact details and confirming ... (best-effort on real site)")
    fill_contact_and_confirm(page, CONTACT)

    context.tracing.stop(path="artifacts/trace.zip")
    context.close()
    browser.close()
    print("Trace saved to artifacts/trace.zip (view with: playwright show-trace artifacts/trace.zip)")

if __name__ == "__main__":
    with sync_playwright() as p:
        run(p)
