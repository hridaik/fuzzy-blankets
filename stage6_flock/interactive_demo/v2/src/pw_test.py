import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "file://" + str(Path(__file__).resolve().parents[1] / "build" / "index.html")
SHOT_DIR = Path(__file__).resolve().parents[1] / "pw_shots"
SHOT_DIR.mkdir(exist_ok=True)

VIEWPORTS = [(1440, 900), (1280, 800), (1100, 720)]

errors = []


def log_console(msg):
    if msg.type == "error":
        errors.append(msg.text)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for vw, vh in VIEWPORTS:
            page = browser.new_page(viewport={"width": vw, "height": vh})
            page.on("console", log_console)
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            page.goto(URL)
            page.wait_for_timeout(400)
            tag = f"{vw}x{vh}"
            print(f"=== {tag} ===")

            for i in range(1, 7):
                btn = page.locator(".tabBtn", has_text=f"{i}.")
                btn.click()
                page.wait_for_timeout(250)
                overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 2")
                print(f"tab{i}: overflow_x={overflow}")
                page.screenshot(path=str(SHOT_DIR / f"{tag}_tab{i}.png"), full_page=True)

            # tab1 interactions
            page.locator(".tabBtn", has_text="1.").click(); page.wait_for_timeout(150)
            page.locator("#stepFwdBtn").click(timeout=2000)
            page.locator("#playBtn").click()
            page.wait_for_timeout(500)
            page.locator("#playBtn").click()
            slider = page.locator("#timeSlider")
            box = slider.bounding_box()
            if box:
                page.mouse.click(box["x"] + box["width"] * 0.7, box["y"] + box["height"] / 2)
            page.wait_for_timeout(150)
            page.screenshot(path=str(SHOT_DIR / f"{tag}_tab1_scrub.png"))

            # tab3 method switch
            page.locator(".tabBtn", has_text="3.").click(); page.wait_for_timeout(150)
            chips = page.locator("#t3Methods .methodChip")
            n = chips.count()
            print("tab3 method chips:", n)
            if n > 1:
                chips.nth(2).click()
                page.wait_for_timeout(150)
            more = page.locator("#t3Methods .moreToggle")
            if more.count():
                more.click()
                page.wait_for_timeout(150)
                print("tab3 chips after more:", page.locator("#t3Methods .methodChip").count())
            page.screenshot(path=str(SHOT_DIR / f"{tag}_tab3_more.png"))

            # tab4 axis change + example click
            page.locator(".tabBtn", has_text="4.").click(); page.wait_for_timeout(150)
            page.locator("#t4X").select_option("C")
            page.wait_for_timeout(150)
            ex = page.locator("#t4Examples .methodChip")
            print("tab4 examples:", ex.count())
            if ex.count() > 1:
                ex.nth(1).click()
                page.wait_for_timeout(150)
            page.screenshot(path=str(SHOT_DIR / f"{tag}_tab4_axis.png"))

            # tab6 seed switch + toggle
            page.locator(".tabBtn", has_text="6.").click(); page.wait_for_timeout(150)
            seeds = page.locator("#t6Seeds .methodChip")
            print("tab6 seeds:", seeds.count())
            if seeds.count() >= 4:
                seeds.nth(3).click()
                page.wait_for_timeout(200)
            page.locator("#stepFwdBtn").click()
            page.locator("#stepFwdBtn").click()
            page.wait_for_timeout(150)
            page.screenshot(path=str(SHOT_DIR / f"{tag}_tab6_seed.png"))

            # provenance drawer
            page.locator("#dataDrawerBtn").click()
            page.wait_for_timeout(150)
            page.screenshot(path=str(SHOT_DIR / f"{tag}_provenance.png"))
            page.locator("#provCloseBtn").click()

            page.close()
        browser.close()

    print("\n=== console/page errors ===")
    if errors:
        for e in errors:
            print("ERR:", e)
    else:
        print("none")


if __name__ == "__main__":
    run()
