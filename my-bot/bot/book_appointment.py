from playwright.sync_api import Playwright, sync_playwright, expect
import sys
import time

# -----------------------------
# CONFIG
# -----------------------------
BASE_URL = "http://localhost:5173"  # your mock-qmatic app
TARGET_TRAMITE = "Asistencia telefónica para la homologación y equivalencia de títulos universitarios extranjeros"

# Contact details to submit
CONTACT = {
    "name": "Monica Pérez Villarroel",
    "id": "Z0428685Q",        # DNI/NIE/Pasaporte
    "email": "monicaperezvillarroel060@gmail.com",
    "phone": "613304514",
}

# Max number of calendar months to scan (including current month)
MAX_MONTHS_TO_SCAN = 6

# -----------------------------
# HELPERS
# -----------------------------
def click_first_sucursal(page):
    # Step 1: choose the first (and only) sucursal
    page.locator('input[name="sucursal"]').first.check()

def select_tramite(page, tramite_text):
    # Step 2: select the trámite by its visible label text
    # Labels have structure: <label class="radio-item"><input ...><span>TEXT</span></label>
    label = page.locator('label.radio-item', has_text=tramite_text).first
    expect(label).to_be_visible()
    label.locator('input[type="radio"]').check()

def find_and_pick_earliest_slot(page):
    """
    Step 3:
    - Iterate months up to MAX_MONTHS_TO_SCAN
    - For each month, click each enabled day
    - If times appear, pick the earliest, return True
    - If none found in all scanned months, return False
    """
    # Ensure Step 3 panel is open
    fecha_panel = page.locator('.panel[data-step="3"]')
    if fecha_panel.get_attribute("aria-expanded") != "true":
        fecha_panel.locator('.hdr').click()

    for month_index in range(MAX_MONTHS_TO_SCAN):
        # Check all enabled day buttons in the grid (.day:not([disabled]))
        day_buttons = page.locator('.daysgrid .day:not([disabled])')
        day_count = day_buttons.count()
        if day_count == 0:
            # No enabled days at all. Move to next month (if any).
            # Click "Siguiente" month arrow:
            next_btn = page.locator('.monthnav .btn', has_text='›')
            if next_btn.is_enabled():
                next_btn.click()
                continue
            else:
                break

        # Iterate through the days in this month
        for i in range(day_count):
            day_btn = day_buttons.nth(i)
            # Click the day
            day_btn.click()

            # After clicking a day, either a .slots list appears or a .muted ("no slots") message shows up
            # Wait a short time for one of them:
            # Use race: wait for either condition with a timeout
            # We'll poll quickly for ~2s
            found_slots = False
            for _ in range(20):
                if page.locator('.slots').count() > 0:
                    found_slots = True
                    break
                if page.locator('.muted').count() > 0:
                    break
                time.sleep(0.1)

            if not found_slots:
                # No slots for this day; try next day
                continue

            # Pick earliest available time (first .slotbtn)
            first_slot = page.locator('.slotbtn').first
            expect(first_slot).to_be_visible()
            first_slot.click()

            # Selection should highlight; Step 4 becomes enabled. Return success.
            return True

        # If we scanned all days in the current month without success, try the next month
        next_btn = page.locator('.monthnav .btn', has_text='›')
        if next_btn.is_enabled():
            next_btn.click()
        else:
            break

    return False

def fill_contact_and_confirm(page, contact):
    # Ensure Step 4 is open/enabled
    step4_panel = page.locator('.panel[data-step="4"]')
    # If disabled, no availability was selected; we shouldn't be here
    assert step4_panel.get_attribute("data-disabled") != "true", "Step 4 is disabled; no slot selected."

    if step4_panel.get_attribute("aria-expanded") != "true":
        step4_panel.locator('.hdr').click()

    # Fill fields
    page.fill('#input_name',  contact["name"])
    page.fill('#input_id',    contact["id"])
    page.fill('#input_email', contact["email"])
    page.fill('#input_phone', contact["phone"])

    # Click Confirmar
    page.locator('.panel[data-step="4"] .btn.primary', has_text="Confirmar").click()

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

    # Accept the cookie bar if present
    if page.locator('#acceptCookies').count() > 0:
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

    # Keep window open a bit (optional)
    time.sleep(2)
    context.close()
    browser.close()

if __name__ == "__main__":
    with sync_playwright() as p:
        run(p)
