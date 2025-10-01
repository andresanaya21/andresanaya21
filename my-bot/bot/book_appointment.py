from playwright.sync_api import Playwright, sync_playwright, expect
import re
import sys
import time
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
BASE_URL = "http://localhost:5173"  # your mock-qmatic app
TARGET_TRAMITE = "Asistencia telefónica para la homologación y equivalencia de títulos universitarios extranjeros"

# Contact details to submit (extended to match the upgraded Step 4)
CONTACT = {
    "name":           "Monica Pérez",
    "lastname":       "Villarroel",
    "id":             "Z0428685Q",             # DNI/NIE/Pasaporte
    "email":          "monicaperezvillarroel060@gmail.com",
    "email_confirm":  "monicaperezvillarroel060@gmail.com",
    "phone_cc":       "+34",
    "phone":          "613304514",
    "phone_confirm":  "613304514",
    "notes":          "Prueba de reserva en el mock",
    "consent":        True,  # required checkbox on the mock (and real site)
}

# Max number of calendar months to scan (including current month)
MAX_MONTHS_TO_SCAN = 6

# How long (seconds) to wait after clicking a day for slots or an empty-state to appear
WAIT_SLOTS_TIMEOUT_S = 4.0


# -----------------------------
# HELPERS
# -----------------------------
def _parse_time_hhmm(t):
    """Return a sortable time from 'HH:MM'."""
    try:
        return datetime.strptime(t.strip(), "%H:%M").time()
    except Exception:
        return datetime.strptime("23:59", "%H:%M").time()


def click_first_sucursal(page):
    # Step 1
    first_radio = page.locator('input[name="sucursal"]').first
    expect(first_radio).to_be_visible()
    first_radio.check()


def select_tramite(page, tramite_text):
    # Step 2
    label = page.locator('label.radio-item', has_text=tramite_text).first
    expect(label).to_be_visible()
    try:
        label.click()
    except Exception:
        label.locator('input[type="radio"]').check()


def _month_label_text(page):
    label = page.locator(".monthnav > div").nth(0)
    return (label.inner_text().strip() if label.count() else "")


def _goto_next_month(page):
    before = _month_label_text(page)
    next_btn = page.locator('.monthnav .btn', has_text='›').first
    if not next_btn.count() or not next_btn.is_enabled():
        return False
    next_btn.click()
    t0 = time.time()
    while time.time() - t0 < 3.0:
        after = _month_label_text(page)
        if after and after != before:
            return True
        time.sleep(0.05)
    return True  # some mock setups redraw without text change


def _wait_for_slots_or_empty(page, timeout_s=WAIT_SLOTS_TIMEOUT_S):
    """Return True if slot buttons appear; False if empty-state appears or timeout."""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if page.locator(".slots .slotbtn, .slotbtn").count() > 0:
            return True
        if page.locator(".emptybox, .muted, .no-slots").count() > 0:
            return False
        time.sleep(0.05)
    return False


def _pick_earliest_slot_on_selected_day(page):
    slots = page.locator(".slotbtn")
    n = slots.count()
    if n == 0:
        return False
    pairs = []
    for i in range(n):
        t_text = slots.nth(i).inner_text().strip()
        m = re.search(r"(\d{1,2}:\d{2})", t_text)
        hhmm = m.group(1) if m else t_text
        pairs.append((_parse_time_hhmm(hhmm), i))
    pairs.sort(key=lambda x: x[0])
    target = slots.nth(pairs[0][1])
    expect(target).to_be_visible()
    target.click()
    return True


def find_and_pick_earliest_slot(page):
    """Open step 3, scan months/days, pick earliest time on first day with availability."""
    fecha_panel = page.locator('.panel[data-step="3"]')
    if fecha_panel.get_attribute("aria-expanded") != "true":
        fecha_panel.locator('.hdr').click()

    for _ in range(MAX_MONTHS_TO_SCAN):
        day_buttons = page.locator('.daysgrid .day:not([disabled])')
        day_count = day_buttons.count()

        if day_count == 0:
            if not _goto_next_month(page):
                break
            continue

        for i in range(day_count):
            day = day_buttons.nth(i)
            try:
                day.click()
            except Exception:
                continue

            if not _wait_for_slots_or_empty(page):
                continue

            if _pick_earliest_slot_on_selected_day(page):
                return True

        if not _goto_next_month(page):
            break

    return False


def _safe_fill(page, selector, value):
    """Fill if the control exists and value is not None/empty. Return True if filled."""
    if value is None or value == "":
        return False
    loc = page.locator(selector)
    if loc.count():
        loc.fill(str(value))
        return True
    return False


def _safe_check(page, selector, checked=True):
    """Check a checkbox/radio if it exists."""
    loc = page.locator(selector)
    if loc.count():
        if checked:
            try:
                loc.check()
            except Exception:
                # some browsers need click on label if check() fails
                try:
                    page.locator(f'label[for="{selector.lstrip("#")}"]').click()
                except Exception:
                    pass
        else:
            try:
                loc.uncheck()
            except Exception:
                pass
        return True
    return False


def _is_enabled(loc):
    try:
        if not loc.count():
            return False
        if not loc.first.is_visible():
            return False
        if not loc.first.is_enabled():
            return False
        # Some UIs also use attributes
        disabled_attr = loc.first.get_attribute("disabled")
        aria_disabled = (loc.first.get_attribute("aria-disabled") or "").lower()
        if disabled_attr not in (None, "", "false"):
            return False
        if aria_disabled in ("true", "1"):
            return False
        return True
    except Exception:
        return False


def click_finish_button(page, timeout_ms=8000):
    """
    Clicks the final Step-4 button:
      - id '#btnAceptar' (mock)
      - text variants 'ACEPTAR' or 'Coger cita'
      - plus generic fallbacks ('Confirmar', 'Guardar aviso', 'Reservar', 'Finalizar')
    Waits for it to become enabled before clicking.
    """
    labels_rx = re.compile(r"(ACEPTAR|Coger\s+cita|Confirmar|Guardar\s+aviso|Reservar|Finalizar)", re.I)

    # Preferred: explicit IDs from the mock
    btn = page.locator("#btnAceptar")
    if not btn.count():
        btn = page.locator("#btnCogerCita")

    # Fallbacks by role/name
    if not btn.count() or not _is_enabled(btn):
        btn = page.get_by_role("button", name=labels_rx).first

    # Fallback by text on button-like elements
    if (not btn.count()) or (not _is_enabled(btn)):
        btn = page.locator("button, [role='button'], input[type=submit]").filter(has_text=labels_rx).first

    # Wait for it to become enabled within the timeout
    end = time.time() + (timeout_ms / 1000.0)
    while time.time() < end:
        if _is_enabled(btn):
            break
        time.sleep(0.05)

    expect(btn).to_be_visible(timeout=timeout_ms)
    # One more guard
    if not _is_enabled(btn):
        raise RuntimeError("Finish button is present but still disabled — form may be incomplete.")

    try:
        btn.click()
    except Exception:
        # last-ditch JS click
        page.evaluate("(el)=>el.click()", btn)

    return True


def fill_contact_and_confirm(page, contact):
    # Step 4 must be enabled after picking a slot
    step4_panel = page.locator('.panel[data-step="4"]')
    assert step4_panel.get_attribute("data-disabled") != "true", "Step 4 is disabled; no slot selected."

    if step4_panel.get_attribute("aria-expanded") != "true":
        step4_panel.locator('.hdr').click()

    # Core fields
    _safe_fill(page, '#input_name',            contact.get("name"))
    _safe_fill(page, '#input_lastname',        contact.get("lastname"))
    _safe_fill(page, '#input_id',              contact.get("id"))
    _safe_fill(page, '#input_email',           contact.get("email"))
    _safe_fill(page, '#input_email_confirm',   contact.get("email_confirm") or contact.get("email"))
    _safe_fill(page, '#input_phone_cc',        contact.get("phone_cc"))
    _safe_fill(page, '#input_phone',           contact.get("phone"))
    _safe_fill(page, '#input_phone_confirm',   contact.get("phone_confirm") or contact.get("phone"))
    _safe_fill(page, '#input_notes',           contact.get("notes"))

    # Consent checkbox (required on the upgraded mock)
    if contact.get("consent", False):
        _safe_check(page, '#input_consent', True)

    # NEW: Click final finish button (ACEPTAR / Coger cita / etc.)
    click_finish_button(page, timeout_ms=8000)

    # Wait for success box
    success = page.locator('#successBox')
    expect(success).to_be_visible(timeout=5000)

    title = page.locator('#successTitle').inner_text()
    msg   = page.locator('#successMsg').inner_text()
    return title, msg


# -----------------------------
# MAIN
# -----------------------------
def run(playwright: Playwright):
    browser = playwright.chromium.launch(headless=False)  # set True to run headless
    context = browser.new_context()
    page = context.new_page()

    print(f"Opening {BASE_URL} ...")
    page.goto(BASE_URL, wait_until="domcontentloaded")

    # Accept cookie bar if present
    if page.locator('#acceptCookies').count():
        page.locator('#acceptCookies').click()

    # Step 1
    click_first_sucursal(page)

    # Step 2
    select_tramite(page, TARGET_TRAMITE)

    # Step 3
    print("Searching for the earliest available day & time ...")
    has_slot = find_and_pick_earliest_slot(page)
    if not has_slot:
        print("No hay citas disponibles (no slots found within the scanned months). Exiting.")
        context.close()
        browser.close()
        sys.exit(2)

    # Step 4
    print("Filling contact details and confirming ...")
    title, msg = fill_contact_and_confirm(page, CONTACT)

    print("\n=== CONFIRMATION ===")
    print(title)
    print(msg)

    time.sleep(1)
    context.close()
    browser.close()


if __name__ == "__main__":
    with sync_playwright() as p:
        run(p)
