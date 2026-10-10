"""Record clean per-tab/per-scenario videos of the v3 interactive demo,
headlessly, via Playwright's built-in video capture. No screen recorder
needed: Chromium renders the page off-screen and Playwright writes the
frames straight to .webm.

Usage:
    python3 record_videos.py            # records everything below
    python3 record_videos.py tab1 tab6  # only the named scenarios

Each scenario drives the SAME DOM the human demo uses (Viz.TL.setT, button
clicks) -- no separate rendering path, so the video always matches what a
viewer sees in the browser. Playback is driven frame-by-frame with a fixed
wait between frames instead of clicking Play, so pacing is deterministic
and immune to setTimeout jitter under video encoding load.
"""
import shutil
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG = None

ROOT = Path(__file__).resolve().parents[1]
URL = "file://" + str(ROOT / "build" / "index.html")
OUT_DIR = ROOT / "videos"
OUT_DIR.mkdir(exist_ok=True)

# Tall enough that every tab's full panel (stage + side cards) fits inside
# the recorded viewport with no scrolling -- measured scrollHeight across
# tabs 1-6 at this width tops out at 1622px (tab1); 1700 leaves margin.
VIEWPORT = {"width": 1440, "height": 1700}


def click_tab(page, n):
    page.locator(".tabBtn").nth(n - 1).click()
    page.wait_for_timeout(200)


def drive_timeline(page, t_start, t_end, ms_per_frame):
    for t in range(t_start, t_end + 1):
        page.evaluate(f"Viz.TL.setT({t})")
        page.wait_for_timeout(ms_per_frame)


def record(pw, name, fn):
    """Runs fn(page) inside a fresh recorded context/page, then saves the
    resulting video as videos/<name>.webm."""
    browser = pw.chromium.launch()
    context = browser.new_context(viewport=VIEWPORT, record_video_dir=str(OUT_DIR), record_video_size=VIEWPORT)
    page = context.new_page()
    page.goto(URL)
    page.wait_for_timeout(300)
    fn(page)
    page.wait_for_timeout(300)
    path = page.video.path()
    page.close()
    context.close()
    browser.close()
    webm = OUT_DIR / f"{name}.webm"
    shutil.move(path, webm)
    if FFMPEG is None:
        print(f"wrote {webm} (install imageio-ffmpeg for automatic .mp4 conversion)")
        return
    mp4 = OUT_DIR / f"{name}.mp4"
    subprocess.run(
        [FFMPEG, "-y", "-i", str(webm), "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-crf", "20", "-preset", "medium", "-movflags", "+faststart", str(mp4)],
        check=True, capture_output=True,
    )
    webm.unlink()
    print(f"wrote {mp4}")


# ---------------------------------------------------------------- scenarios

def scenario_tab1(page):
    click_tab(page, 1)
    # identify = 41 (data-driven); play through the observation window and
    # stop a handful of steps after the boundary/interior appear.
    drive_timeline(page, 0, 41 + 7, 160)


def scenario_tab2(page):
    click_tab(page, 2)
    # Static analytic snapshot (no timeline): cycle taus, then the causal-
    # effect toggle, to show the top-5 highlighted birds shift each time.
    for tau_label in ["2", "4", "8"]:
        page.locator("#t2Toggles .methodChip", has_text=tau_label).last.click()
        page.wait_for_timeout(2200)
    page.locator("#t2Toggles .methodChip", has_text="Direct causal effect").click()
    page.wait_for_timeout(2200)
    # back to authority, tau=2, as the settled end-state
    page.locator("#t2Toggles .methodChip", has_text="Target authority").click()
    page.wait_for_timeout(1200)


def scenario_tab3(page):
    click_tab(page, 3)
    # Default method is already "Our Method" (sparse interface multicover,
    # V3) -- leave method selection untouched, just play start to release.
    drive_timeline(page, 0, 46, 150)


def scenario_tab4(page):
    click_tab(page, 4)
    categories = ["Compact clump", "Coherent but hollow", "Snake-like connected", "Weak / noisy"]
    for cat in categories:
        btn = page.locator("#t4Examples .methodChip", has_text=cat)
        if btn.count() == 0:
            continue
        btn.click()
        page.wait_for_timeout(600)
        thumbs = page.locator("#t4ExampleStrip .miniThumb")
        n = thumbs.count()
        for i in range(n):
            thumbs.nth(i).click()
            page.wait_for_timeout(1800)


def scenario_tab5(page):
    click_tab(page, 5)
    drive_timeline(page, 0, 99, 130)


def scenario_tab6_seed(seed_index, label):
    def fn(page):
        click_tab(page, 6)
        chips = page.locator("#t6Seeds .methodChip")
        chips.nth(seed_index).click()
        page.wait_for_timeout(300)
        drive_timeline(page, 0, 47, 160)
    fn.__name__ = f"tab6_{label}"
    return fn


SCENARIOS = {
    "tab1": scenario_tab1,
    "tab2": scenario_tab2,
    "tab3": scenario_tab3,
    "tab4": scenario_tab4,
    "tab5": scenario_tab5,
}

TAB6_SEEDS = [
    "612c02_a357_strong_success",
    "sclosure02_a270_split",
    "sclosure00_a313_failure",
    "612c06_a17_failure_ordinary",
    "612c01_a266_kinematic_top_negative",
]
for i, label in enumerate(TAB6_SEEDS):
    SCENARIOS[f"tab6_{label}"] = scenario_tab6_seed(i, label)


def main():
    names = sys.argv[1:] or list(SCENARIOS.keys())
    with sync_playwright() as pw:
        for name in names:
            if name not in SCENARIOS:
                print(f"unknown scenario: {name}", file=sys.stderr)
                continue
            record(pw, name, SCENARIOS[name])


if __name__ == "__main__":
    main()
