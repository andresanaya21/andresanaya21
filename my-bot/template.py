# pip install playwright
# playwright install

import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

BOOKING_URL = "https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/"

# ---- Your preferences here ----
SERVICE_TEXT = "Asistencia telefónica para la homologación y equivalencia de títulos universitarios extranjeros"        # e.g., "Trámites X" (replace with the exact visible text)
OFFICE_TEXT  = "Seleccione oficina"         # e.g., "Madrid - Oficina Y"
LOCATION_TEXT = None                        # Set if there’s an extra step (or keep None)
PREFERRED_DATE = None                       # e.g., "2025-10-15" (YYYY-MM-DD) or None for earliest
USER = {
    "name": "Monica Pérez Villarroel",
    "id": "Z0428685Q",        # DNI/NIE/Pasaporte
    "email": "monicaperezvillarroel060@gmail.com",
    "phone": "613304514",
}

async def wait_ready(page):
    # wait for network to be mostly idle and the app shell to render
    await page.wait_for_load_state("domcontentloaded")
    await page.wait_for_load_state("networkidle")

async def accept_cookies_if_present(page):
    for text in ["Aceptar", "Aceptar todo", "Aceptar cookies", "Consentir"]:
        try:
            await page.get_by_role("button", name=text, exact=False).click(timeout=2000)
            break
        except PlaywrightTimeoutError:
            pass

async def choose_by_label(page, label_text, option_text):
    # For dropdowns or cards with visible text
    # Try click card with text; if it’s a select, open then select option
    try:
        # card/button style
        await page.get_by_role("button", name=option_text, exact=False).click(timeout=2500)
        return
    except PlaywrightTimeoutError:
        pass
    try:
        # labeled select pattern
        label = page.get_by_text(label_text, exact=False).first
        await label.click(timeout=2500)
    except PlaywrightTimeoutError:
        pass
    try:
        await page.get_by_role("combobox").first.click(timeout=2000)
        await page.get_by_role("option", name=option_text, exact=False).click(timeout=3000)
        return
    except PlaywrightTimeoutError:
        # Fallback: click by visible text anywhere
        await page.get_by_text(option_text, exact=False).first.click(timeout=3000)

async def pick_earliest_date(page):
    # Looks for enabled calendar buttons (not disabled) and clicks the first
    # Assumes the date elements are role=button with the day number
    # Adjust if the site uses a different calendar widget.
    day_candidates = await page.locator("button:enabled").all()
    for btn in day_candidates:
        txt = (await btn.inner_text()).strip()
        if txt.isdigit():
            await btn.click()
            return True
    return False

async def pick_specific_date(page, yyyy_mm_dd):
    # Naive example: step months until the target appears; adjust selectors to your calendar widget.
    # Parse target day
    y, m, d = yyyy_mm_dd.split("-")
    target_day = str(int(d))
    for _ in range(12):  # cap to 12 months lookahead
        try:
            await page.get_by_role("button", name=target_day, exact=True).click(timeout=1200)
            return True
        except PlaywrightTimeoutError:
            # click next month arrow; adjust selector if needed
            try:
                # common labels: "Siguiente", "Next month", ">"
                await page.get_by_role("button", name="Siguiente", exact=False).click(timeout=1200)
            except PlaywrightTimeoutError:
                # fallback to an arrow button
                await page.locator("button[aria-label*='Next'], button:has-text('>')").first.click(timeout=1200)
    return False

async def pick_time_slot(page):
    # Time slots often appear as buttons with times like "10:20"
    # Click the first enabled one; adapt to your needs
    slots = page.locator("button:enabled").filter(has_text=":")  # crude filter for "HH:MM"
    count = await slots.count()
    if count == 0:
        return False
    await slots.nth(0).click()
    return True

async def fill_personal_data(page, user):
    # Adjust field placeholders/labels to match the site
    try:
        await page.get_by_label("Nombre", exact=False).fill(user["name"])
    except:
        await page.get_by_placeholder("Nombre", exact=False).fill(user["name"])
    try:
        await page.get_by_label("DNI", exact=False).fill(user["id"])
    except:
        await page.get_by_placeholder("DNI", exact=False).fill(user["id"])
    try:
        await page.get_by_label("Correo", exact=False).fill(user["email"])
    except:
        await page.get_by_placeholder("Correo", exact=False).fill(user["email"])
    try:
        await page.get_by_label("Teléfono", exact=False).fill(user["phone"])
    except:
        await page.get_by_placeholder("Teléfono", exact=False).fill(user["phone"])

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        await page.goto(BOOKING_URL, wait_until="domcontentloaded")
        await wait_ready(page)
        await accept_cookies_if_present(page)

        # 1) Choose service
        if SERVICE_TEXT:
            await choose_by_label(page, "Servicio", SERVICE_TEXT)
        # 2) Choose office
        if OFFICE_TEXT:
            await choose_by_label(page, "Oficina", OFFICE_TEXT)
        # 3) Optional: location/municipality
        if LOCATION_TEXT:
            await choose_by_label(page, "Localidad", LOCATION_TEXT)

        # Continue / Next
        # Adjust these to match the site’s “Next/Continuar/Siguiente” buttons
        for _ in range(2):
            try:
                await page.get_by_role("button", name="Siguiente", exact=False).click(timeout=2500)
                await wait_ready(page)
            except PlaywrightTimeoutError:
                break

        # 4) Pick date
        ok = False
        if PREFERRED_DATE:
            ok = await pick_specific_date(page, PREFERRED_DATE)
        if not ok:
            ok = await pick_earliest_date(page)
        if not ok:
            print("No available dates found right now.")
            await context.close(); await browser.close(); return

        # 5) Pick time
        if not await pick_time_slot(page):
            print("No available time slots for selected date.")
            await context.close(); await browser.close(); return

        # Continue
        try:
            await page.get_by_role("button", name="Siguiente", exact=False).click(timeout=2500)
        except PlaywrightTimeoutError:
            pass

        # 6) Fill personal data
        await fill_personal_data(page, USER)

        # --- MANUAL CAPTCHA STEP (if present) ---
        print("If there is a CAPTCHA, solve it now. Then press the Confirm button manually, or uncomment click below.")
        # Uncomment if there is a clearly labeled confirm button and no captcha
        # await page.get_by_role("button", name="Confirmar", exact=False).click()

        # Wait for confirmation page (adjust the text to a confirmation keyword)
        try:
            await page.get_by_text("confirmación", exact=False).wait_for(timeout=20000)
        except PlaywrightTimeoutError:
            pass

        # Save proof
        await page.screenshot(path="cita_confirmacion.png", full_page=True)
        print("Saved screenshot: cita_confirmacion.png")

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
