import os
import sys
import glob
import time
import subprocess
import argparse
import requests
from googleapiclient.discovery import build

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

def get_media_duration(file_path):
    """Utility function to get duration of audio/video using ffprobe"""
    if not os.path.exists(file_path):
        return 0.0
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())
    except Exception as e:
        print(f"⚠️ Error probing duration for {file_path}: {e}")
        return 0.0

def run_gk6_asset_auditor(project_dir, character_name="", max_wait_attempts=3):
    """
    Gatekeeper 6 Auditor: Ensures 100% audio parts and keyframe images are present before rendering.
    Includes a 3-attempt Grace Period with Google Drive resync to prevent premature race condition failures.
    """
    media_dir = os.path.join(project_dir, "02.Media Generation")
    audio_dir = os.path.join(media_dir, "audio")
    keyframes_dir = os.path.join(media_dir, "keyframes")

    print(f"\n--- Phase 4: Gatekeeper 6 Asset Auditor for {os.path.basename(project_dir)} ---")

    for attempt in range(1, max_wait_attempts + 1):
        missing_audio = []
        for p in range(1, 16):
            wav_path = os.path.join(audio_dir, f"Part_{p:02d}_Voiceover.wav")
            if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 10240:
                matches = [f for f in glob.glob(os.path.join(audio_dir, f"*Part_{p:02d}*.wav")) if os.path.getsize(f) >= 10240]
                if not matches:
                    missing_audio.append(p)

        image_files = [f for f in (glob.glob(os.path.join(keyframes_dir, "*.jpg")) + glob.glob(os.path.join(keyframes_dir, "*.png"))) if os.path.getsize(f) >= 30720]

        if not missing_audio and len(image_files) >= 15:
            print(f"✅ [GK6 PASSED] Verified 15/15 Audio Parts and {len(image_files)} Keyframe Images (Attempt {attempt}/{max_wait_attempts}).")
            return True

        if attempt < max_wait_attempts:
            print(f"⏳ [GK6 GRACE PERIOD] Assets still syncing (Audio missing: {missing_audio}, Images: {len(image_files)}/15). Waiting 8s for in-flight uploads... (Attempt {attempt}/{max_wait_attempts})")
            time.sleep(8)
            try:
                from gdrive_utils import sync_project_from_gdrive
                if character_name:
                    sync_project_from_gdrive(character_name, project_dir)
            except Exception:
                pass

    if missing_audio:
        print(f"⛔ [GK6 REJECTED] Missing or corrupt audio for Parts: {missing_audio}")
        return False

    if len(image_files) < 15:
        print(f"⛔ [GK6 REJECTED] Found only {len(image_files)} valid keyframe images (minimum 15 required).")
        return False

    return True

def render_part_video(part_num, wav_path, part_images, output_part_mp4):
    """
    Renders an individual Part Video with Ken Burns pan/zoom on its corresponding keyframes.
    Keeps RAM usage under 150MB per part.
    """
    part_dur = get_media_duration(wav_path)
    if part_dur <= 0:
        print(f"⛔ Cannot render Part {part_num:02d}: Audio duration is 0s.")
        return False

    if not part_images:
        print(f"⛔ Cannot render Part {part_num:02d}: No images allocated.")
        return False

    num_imgs = len(part_images)
    img_dur = part_dur / num_imgs
    fps = 25

    inputs = []
    filter_complex = []

    for idx, img in enumerate(part_images):
        inputs.extend(["-loop", "1", "-t", str(img_dur), "-i", img])
        total_frames = int(img_dur * fps)
        if idx % 2 == 0:
            # Slow zoom in
            zoom_expr = f"zoompan=z='min(zoom+0.0012,1.20)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s=1920x1080:fps={fps}"
        else:
            # Slow zoom out
            zoom_expr = f"zoompan=z='max(1.20-0.0012*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s=1920x1080:fps={fps}"
        filter_complex.append(f"[{idx}:v]{zoom_expr}[v{idx}]")

    concat_inputs = "".join([f"[v{i}]" for i in range(num_imgs)])
    filter_complex.append(f"{concat_inputs}concat=n={num_imgs}:v=1:a=0[vfinal]")

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-i", wav_path,
        "-filter_complex", ";".join(filter_complex),
        "-map", "[vfinal]", "-map", f"{num_imgs}:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        output_part_mp4
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"⛔ FFmpeg error rendering Part {part_num:02d}: {res.stderr[-300:]}")
        return False

    return os.path.exists(output_part_mp4) and os.path.getsize(output_part_mp4) > 10240

def build_kenburns_video(project_dir, output_mp4_path):
    """
    METHOD 1: Part-by-Part Video Assembly & Fast Concat
    1. Renders Part 01.mp4 ... Part 15.mp4 individually (lightweight RAM, fast).
    2. Concat 15 parts with 5.0s silence transitions in 10 seconds.
    """
    media_dir = os.path.join(project_dir, "02.Media Generation")
    audio_dir = os.path.join(media_dir, "audio")
    keyframes_dir = os.path.join(media_dir, "keyframes")
    video_parts_dir = os.path.join(media_dir, "video_parts")
    final_dir = os.path.join(project_dir, "03.Final Production")

    os.makedirs(video_parts_dir, exist_ok=True)
    os.makedirs(final_dir, exist_ok=True)

    character_name = os.path.basename(os.path.normpath(project_dir))
    print(f"\n--- Phase 4: Method 1 Part-by-Part Video Assembly for {character_name} ---")

    # Pull assets from GDrive if missing & set Sheet status to Producing
    try:
        from gdrive_utils import sync_project_from_gdrive, get_gdrive_service, ensure_project_tree, upload_file
        sync_project_from_gdrive(character_name, project_dir)
        gdrive_service = get_gdrive_service()
        tree = ensure_project_tree(gdrive_service, character_name) if gdrive_service else {}

        if gdrive_service:
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
                sheets_svc.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"Pipeline!D{row_idx}",
                    valueInputOption="USER_ENTERED",
                    body={"values": [["Producing"]]}
                ).execute()
    except Exception as ge:
        print(f"⚠️ GDrive / Sheet Notice: {ge}")
        gdrive_service = None
        tree = {}
        row_idx = None

    # Run GK6 Asset Audit (with 3-attempt resync grace period)
    if not run_gk6_asset_auditor(project_dir, character_name=character_name):
        print("⛔ [GK6 HALT] Assets are not complete. Halting assembly to prevent broken video.")
        notify_cloudflare("GK_ERROR", character_name, {
            "gk": "GK6",
            "reason": "GK6 Asset audit rejected: Incomplete audio parts or keyframe images."
        })
        sys.exit(1)

    all_images = sorted(glob.glob(os.path.join(keyframes_dir, "*.jpg"))) + sorted(glob.glob(os.path.join(keyframes_dir, "*.png")))
    notify_cloudflare("GK6_VERIFIED", character_name, {
        "audio_count": 15,
        "img_count": len(all_images)
    })

    rendered_parts = []

    # Step 1: Render each Part Video individually
    for p in range(1, 16):
        part_str = f"{p:02d}"
        wav_path = os.path.join(audio_dir, f"Part_{part_str}_Voiceover.wav")
        if not os.path.exists(wav_path):
            matches = glob.glob(os.path.join(audio_dir, f"*Part_{part_str}*.wav"))
            if matches:
                wav_path = matches[0]

        if not os.path.exists(wav_path):
            print(f"⚠️ Skipping Part {part_str}: Audio WAV not found.")
            continue

        # Get images specifically matching beat_PXX_* or slice from all_images
        part_imgs = [img for img in all_images if f"P{part_str}_" in os.path.basename(img) or f"Part_{part_str}" in os.path.basename(img)]
        if not part_imgs:
            # Fallback evenly across all images
            imgs_per_part = max(1, len(all_images) // 15)
            start_idx = (p - 1) * imgs_per_part
            end_idx = start_idx + imgs_per_part if p < 15 else len(all_images)
            part_imgs = all_images[start_idx:end_idx] if start_idx < len(all_images) else [all_images[-1]]

        part_mp4_path = os.path.join(video_parts_dir, f"Part_{part_str}_Video.mp4")

        # Skip if already rendered and valid
        if os.path.exists(part_mp4_path) and get_media_duration(part_mp4_path) > 10.0:
            print(f"⏩ Part {part_str} Video already exists. Skipping render.")
            rendered_parts.append((p, part_mp4_path))
            continue

        print(f"🎬 [{p}/15] Rendering Part {part_str} Video ({len(part_imgs)} keyframes)...")
        t0 = time.time()
        success = render_part_video(p, wav_path, part_imgs, part_mp4_path)
        if success:
            dur = get_media_duration(part_mp4_path)
            print(f"  └─ ✅ Part {part_str} Rendered in {time.time()-t0:.1f}s | Duration: {dur:.1f}s")
            rendered_parts.append((p, part_mp4_path))
        else:
            print(f"  └─ ❌ Failed to render Part {part_str}.")

    if not rendered_parts:
        print("[Error] Zero part videos were rendered successfully.")
        sys.exit(1)

    # Step 2: Create 5.0s black silence transition
    silence_mp4_path = os.path.join(video_parts_dir, "silence_5s.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1920x1080:d=5:r=25",
        "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", "5",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
        "-c:a", "aac", "-b:a", "192k",
        silence_mp4_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    # Step 3: Fast Concat all Parts into Master MP4
    concat_list_file = os.path.join(final_dir, "concat_video_parts.txt")
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for idx, (_, path) in enumerate(rendered_parts):
            f.write(f"file '{path}'\n")
            if idx < len(rendered_parts) - 1 and os.path.exists(silence_mp4_path):
                f.write(f"file '{silence_mp4_path}'\n")

    print(f"\n🚀 Fast Concatenating {len(rendered_parts)} Video Parts into Master Video...")
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_file,
        "-c", "copy",
        output_mp4_path
    ]
    subprocess.run(cmd_concat, check=True)
    print(f"🎉 Master Video Created: {output_mp4_path}")

    # GK7 Quality Check & Upload
    final_dur = get_media_duration(output_mp4_path)
    file_size_mb = os.path.getsize(output_mp4_path) / (1024 * 1024) if os.path.exists(output_mp4_path) else 0

    if final_dur > 0 and file_size_mb > 10:
        print(f"✅ [GK7 PASSED] Final Master Video Duration: {final_dur:.2f}s ({final_dur/60:.1f} minutes) | Size: {file_size_mb:.1f}MB")
        final_url = ""
        if gdrive_service and tree.get("final_id"):
            final_id = upload_file(gdrive_service, output_mp4_path, parent_id=tree["final_id"])
            if final_id and row_idx:
                final_url = f"https://drive.google.com/file/d/{final_id}/view"
                sheets_svc.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"Pipeline!J{row_idx}",
                    valueInputOption="USER_ENTERED",
                    body={"values": [[final_url]]}
                ).execute()

                sheets_svc.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"Pipeline!D{row_idx}",
                    valueInputOption="USER_ENTERED",
                    body={"values": [["Done"]]}
                ).execute()
                print(f"🎉 Updated Sheet Row {row_idx}: Status=Done, Video Link={final_url}")

        # Bắn Signal GK7_PASSED sang Cloudflare Worker
        notify_cloudflare("ASSEMBLY_COMPLETED", character_name, {
            "status": "SUCCESS",
            "duration": round(final_dur, 2),
            "file_size_mb": round(file_size_mb, 2),
            "video_url": final_url
        })
    else:
        print(f"⛔ [GK7 FAILED] Video duration is 0s or file empty for {output_mp4_path}")
        notify_cloudflare("GK_ERROR", character_name, {
            "gk": "GK7",
            "reason": f"Final video validation failed (Duration: {final_dur}s, Size: {file_size_mb}MB)"
        })
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ken Burns Part-by-Part Video Assembly for HistorySnooze")
    parser.add_argument("--project_dir", required=True, help="Project directory path")
    parser.add_argument("--output_mp4", required=True, help="Target output MP4 file path")
    args = parser.parse_args()

    build_kenburns_video(args.project_dir, args.output_mp4)
