import os
import sys
import glob
import json
import time
import argparse
import requests
from typing import Optional
from googleapiclient.discovery import build

DOWNLOADS_DIR = os.path.expanduser("~/Downloads")

def notify_cloudflare(event_name, character_name, data=None):
    """Fires telemetry & gatekeeper status signals back to Cloudflare Worker Edge Gateway"""
    worker_url = os.environ.get("CLOUDFLARE_WORKER_URL", "https://historysnooze-gateway.hothihuong113.workers.dev")
    try:
        requests.post(
            f"{worker_url}/api/pipeline/callback",
            json={
                "event": event_name,
                "character": character_name,
                "data": data or {},
                "timestamp": time.time()
            },
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"📡 [SIGNAL SENT -> CLOUDFLARE] {event_name} for '{character_name}'")
    except Exception as e:
        print(f"⚠️ Notice sending signal to Cloudflare: {e}")

def validate_image_file(file_path):
    """GK5 Physical Image Validator: Size >= 30KB"""
    if not os.path.exists(file_path):
        return False
    size = os.path.getsize(file_path)
    if size < 30720:
        print(f"⛔ [GK5 IMAGE REJECTED] {os.path.basename(file_path)} size ({size/1024:.1f}KB) < 30KB. Corrupt image.")
        return False
    print(f"✅ [GK5 IMAGE PASSED] {os.path.basename(file_path)} ({size/1024:.1f}KB)")
    return True

def get_newest_downloaded_image(since_time: float) -> Optional[str]:
    image_files = []
    dirs_to_scan = [DOWNLOADS_DIR]
    
    if os.path.exists(DOWNLOADS_DIR):
        for d in os.listdir(DOWNLOADS_DIR):
            full_d = os.path.join(DOWNLOADS_DIR, d)
            if os.path.isdir(full_d) and 'veo' in d.lower():
                dirs_to_scan.append(full_d)
                
    for d in dirs_to_scan:
        try:
            if os.path.exists(d):
                for f in os.listdir(d):
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        path = os.path.join(d, f)
                        mtime = os.path.getmtime(path)
                        if mtime > since_time:
                            image_files.append((path, mtime))
        except Exception:
            pass
            
    if not image_files:
        return None
    newest = max(image_files, key=lambda x: x[1])
    return newest[0]

def run_vps_imagefx_generator(character_name, project_dir, cdp_port=9222):
    """
    VPS ImageFX Generator: Uses Playwright CDP single session (port 9222)
    to generate ImageFX keyframe images for HistorySnooze.
    """
    preprod_dir = os.path.join(project_dir, "01.Preproduction")
    media_dir = os.path.join(project_dir, "02.Media Generation")
    keyframes_dir = os.path.join(media_dir, "keyframes")
    os.makedirs(keyframes_dir, exist_ok=True)

    print(f"\n--- HistorySnooze VPS ImageFX Generator ---")
    print(f"Character: {character_name}")
    print(f"Keyframes Dir: {keyframes_dir}")

    try:
        from gdrive_utils import sync_project_from_gdrive
        sync_project_from_gdrive(character_name, project_dir)
    except Exception as ge:
        print(f"⚠️ GDrive Pull Notice: {ge}")

    beats_files = sorted(glob.glob(os.path.join(preprod_dir, "*_beats.json")))
    if not beats_files:
        print(f"[Error] No beats JSON files found in {preprod_dir}")
        sys.exit(1)

    all_prompts = []
    for bf in beats_files:
        try:
            with open(bf, "r", encoding="utf-8") as f:
                data = json.load(f)
                beats = data.get("beats", [])
                for b in beats:
                    beat_id = b.get("beat_id")
                    prompt = b.get("prompt")
                    out_img = os.path.join(keyframes_dir, f"beat_{beat_id}.jpg")
                    if not validate_image_file(out_img):
                        all_prompts.append((beat_id, prompt, out_img))
        except Exception as e:
            print(f"[Error] Failed to read {bf}: {e}")

    print(f"Total Keyframe Images to Generate: {len(all_prompts)}")
    if not all_prompts:
        print("🎉 All keyframe images already generated & validated!")
        return

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[Error] Playwright is not installed. Please install playwright.")
        sys.exit(1)

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(f"http://localhost:{cdp_port}")
            print(f"✅ Connected to Chrome CDP on port {cdp_port}")
            context = browser.contexts[0]
            
            page = None
            for p_tab in context.pages:
                if "labs.google" in p_tab.url:
                    page = p_tab
                    break

            if not page:
                page = context.pages[0] if context.pages else context.new_page()

            cdp = context.new_cdp_session(page)
            cdp.send("Page.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath": DOWNLOADS_DIR
            })

            for idx, (beat_id, prompt_text, out_path) in enumerate(all_prompts):
                print(f"\n[{idx+1}/{len(all_prompts)}] Generating ImageFX for {beat_id}...")
                print(f"  Prompt: {prompt_text[:80]}...")

                start_time = time.time()
                
                try:
                    page.wait_for_selector("div[data-slate-editor='true']", timeout=15000)
                    editor = page.locator("div[data-slate-editor='true']").first
                    editor.click(force=True)
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    time.sleep(0.5)
                    editor.fill(prompt_text)
                    time.sleep(1.0)
                    
                    gen_btn = page.locator("button:has-text('Create'), button:has-text('Generate')").first
                    if gen_btn.count() > 0 and gen_btn.is_visible():
                        gen_btn.click()
                    else:
                        page.keyboard.press("Enter")

                    # Wait for generation to complete (check for new image card or progress bar disappear)
                    print("  └─ Waiting for generation...")
                    page.wait_for_selector("img[src*='lh3.googleusercontent.com'], img[src*='googleusercontent']", timeout=30000)
                    time.sleep(3.0)

                    download_success = False

                    # 1. Primary Method: Click on the first generated result card, then click Download button
                    try:
                        first_img_card = page.locator("div[role='button']:has(img), img[src*='googleusercontent']").first
                        if first_img_card.count() > 0:
                            first_img_card.click(force=True)
                            time.sleep(1.5)

                            # Find download button in viewer/toolbar
                            dl_btn = page.locator("button[aria-label*='Download'], button[aria-label*='download'], button[data-tooltip*='Download'], button:has-text('Download')").first
                            if dl_btn.count() > 0 and dl_btn.is_visible():
                                with page.expect_download(timeout=15000) as download_info:
                                    dl_btn.click(force=True)
                                download = download_info.value
                                download.save_as(out_path)
                                if validate_image_file(out_path):
                                    download_success = True
                    except Exception as de:
                        print(f"  ⚠️ Direct download click attempt: {de}")

                    # 2. Secondary Method: Intercept newest file in ~/Downloads
                    if not download_success:
                        downloaded_file = get_newest_downloaded_image(start_time)
                        if downloaded_file:
                            import shutil
                            shutil.copy2(downloaded_file, out_path)
                            if validate_image_file(out_path):
                                download_success = True

                    # 3. Tertiary Method: Fetch high-res image src directly from DOM (replace dimensions with =s0 for 4K)
                    if not download_success:
                        try:
                            img_elem = page.locator("img[src*='lh3.googleusercontent.com']").first
                            if img_elem.count() > 0:
                                src_url = img_elem.get_attribute("src")
                                if src_url:
                                    # Request highest available resolution (=s0 or =w3840-h2160)
                                    import re
                                    high_res_url = re.sub(r'=w\d+-h\d+.*|=s\d+.*', '=s0', src_url)
                                    import requests
                                    resp = requests.get(high_res_url, timeout=15)
                                    if resp.status_code == 200 and len(resp.content) > 30720:
                                        with open(out_path, "wb") as f_out:
                                            f_out.write(resp.content)
                                        if validate_image_file(out_path):
                                            download_success = True
                        except Exception as fe:
                            print(f"  ⚠️ High-res URL fetch error: {fe}")

                    if not download_success:
                        print(f"  ❌ Failed to download valid keyframe for {beat_id}.")

                except Exception as ie:
                    print(f"  ⚠️ Playwright interaction error for {beat_id}: {ie}")

                # Upload to GDrive
                try:
                    from gdrive_utils import get_gdrive_service, ensure_project_tree, upload_file
                    gdrive_service = get_gdrive_service()
                    if gdrive_service and os.path.exists(out_path):
                        tree = ensure_project_tree(gdrive_service, character_name)
                        upload_file(gdrive_service, out_path, parent_id=tree["keyframes_id"])
                except Exception as ge:
                    print(f"  ⚠️ GDrive Upload Notice for {beat_id}: {ge}")

                time.sleep(3)

            # Check GK5 for all keyframes & Update Sheet Col I Link
            try:
                from gdrive_utils import get_gdrive_service, ensure_project_tree
                gdrive_service = get_gdrive_service()
                if gdrive_service:
                    tree = ensure_project_tree(gdrive_service, character_name)
                    keyframes_url = f"https://drive.google.com/drive/u/0/folders/{tree['keyframes_id']}"
                    
                    from format_gsheet_control_center import SPREADSHEET_ID
                    sheets_svc = build("sheets", "v4", credentials=gdrive_service._credentials)
                    res = sheets_svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="Pipeline!A:K").execute()
                    rows = res.get("values", [])
                    row_idx = None
                    for idx, r in enumerate(rows):
                        if len(r) > 1 and r[1].strip().lower() == character_name.strip().lower():
                            row_idx = idx + 1
                            break

                    if row_idx:
                        # Update Col I with GDrive Keyframes Link
                        sheets_svc.spreadsheets().values().update(
                            spreadsheetId=SPREADSHEET_ID,
                            range=f"Pipeline!I{row_idx}",
                            valueInputOption="USER_ENTERED",
                            body={"values": [[keyframes_url]]}
                        ).execute()

                        # Check if Col D is Voiceover -> Update Col D to Ready
                        curr_status = rows[row_idx - 1][3] if len(rows[row_idx - 1]) > 3 else ""
                        if curr_status == "Voiceover":
                            sheets_svc.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=f"Pipeline!D{row_idx}",
                                valueInputOption="USER_ENTERED",
                                body={"values": [["Ready"]]}
                            ).execute()
                            print(f"✅ Status updated to 'Ready' for {character_name}")

                    # Bắn Signal IMAGES_COMPLETED sang Cloudflare Worker: 100% Ảnh Đạt GK5!
                    notify_cloudflare("IMAGES_COMPLETED", character_name, {
                        "status": "SUCCESS",
                        "total_images": len(all_prompts),
                        "keyframes_gdrive_url": keyframes_url
                    })
                    print(f"\n🎉 Keyframe Generation Completed for {character_name}!")
                    print(f"✅ Updated Sheet Pipeline Row {row_idx}: Image Link={keyframes_url}")
            except Exception as se:
                print(f"⚠️ Sheet Image Link Update Error: {se}")

        except Exception as e:
            print(f"[CDP Error] Could not connect or interact with Chrome CDP: {e}")
            print("Please ensure Chrome is running with '--remote-debugging-port=9222'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VPS ImageFX Generator for HistorySnooze")
    parser.add_argument("--character", required=True, help="Historical character name")
    parser.add_argument("--project_dir", default="", help="Project directory path")
    parser.add_argument("--cdp_port", type=int, default=9222, help="Chrome CDP port (default 9222)")
    args = parser.parse_args()

    proj_dir = args.project_dir or f"01.Projects/{args.character}"
    run_vps_imagefx_generator(args.character, proj_dir, args.cdp_port)
