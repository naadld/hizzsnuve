import os
import sys
import glob
import time
import subprocess
import argparse
from googleapiclient.discovery import build

def get_audio_duration(file_path):
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

def run_gk6_asset_auditor(project_dir):
    """
    Gatekeeper 6 Auditor: Ensures 100% audio parts and keyframe images are present before rendering.
    """
    media_dir = os.path.join(project_dir, "02.Media Generation")
    audio_dir = os.path.join(media_dir, "audio")
    keyframes_dir = os.path.join(media_dir, "keyframes")

    print(f"\n--- Phase 4: Gatekeeper 6 Asset Auditor for {os.path.basename(project_dir)} ---")

    # Check Audio Parts
    missing_audio = []
    for p in range(1, 16):
        wav_path = os.path.join(audio_dir, f"Part_{p:02d}_Voiceover.wav")
        if not os.path.exists(wav_path):
            matches = glob.glob(os.path.join(audio_dir, f"*Part_{p:02d}*.wav"))
            if not matches:
                missing_audio.append(p)

    if missing_audio:
        print(f"⛔ [GK6 REJECTED] Missing audio for Parts: {missing_audio}")
        return False

    # Check Keyframe Images
    image_files = glob.glob(os.path.join(keyframes_dir, "*.jpg")) + glob.glob(os.path.join(keyframes_dir, "*.png"))
    if len(image_files) < 15:
        print(f"⛔ [GK6 REJECTED] Found only {len(image_files)} keyframe images (minimum 15 required).")
        return False

    print(f"✅ [GK6 PASSED] Found 15/15 Audio Parts and {len(image_files)} Keyframe Images.")
    return True

def build_kenburns_video(project_dir, output_mp4_path):
    """
    Assembles final video using Ken Burns pan/zoom effect from static images + audio.
    """
    preprod_dir = os.path.join(project_dir, "01.Preproduction")
    media_dir = os.path.join(project_dir, "02.Media Generation")
    audio_dir = os.path.join(media_dir, "audio")
    keyframes_dir = os.path.join(media_dir, "keyframes")
    final_dir = os.path.join(project_dir, "03.Final Production")
    os.makedirs(final_dir, exist_ok=True)

    character_name = os.path.basename(os.path.normpath(project_dir))
    print(f"\n--- Phase 4: Ken Burns Video Assembly Engine for {character_name} ---")

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

    # Run GK6 Audit
    if not run_gk6_asset_auditor(project_dir):
        print("⚠️ Warning: Asset auditor did not pass all checks. Attempting partial assembly...")

    # Collect audio files & images per part
    concat_list_file = os.path.join(final_dir, "concat_audio_list.txt")
    audio_files = []
    
    for p in range(1, 16):
        wav_path = os.path.join(audio_dir, f"Part_{p:02d}_Voiceover.wav")
        if not os.path.exists(wav_path):
            matches = glob.glob(os.path.join(audio_dir, f"*Part_{p:02d}*.wav"))
            if matches:
                wav_path = matches[0]

        if os.path.exists(wav_path):
            audio_files.append((p, wav_path))

    if not audio_files:
        print("[Error] No audio files found in audio directory. Cannot assemble.")
    # Create 5.0s silence wav file for spacing between parts
    silence_5s_path = os.path.join(final_dir, "silence_5s.wav")
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", "5", "-c:a", "pcm_s16le", silence_5s_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    # Write concat list for ffmpeg with 5.0s pause between parts
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for idx, (_, path) in enumerate(audio_files):
            f.write(f"file '{path}'\n")
            if idx < len(audio_files) - 1 and os.path.exists(silence_5s_path):
                f.write(f"file '{silence_5s_path}'\n")

    # Combine full audio
    combined_audio = os.path.join(final_dir, "combined_voiceover.wav")
    cmd_audio = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_file, "-c:a", "pcm_s16le", combined_audio
    ]
    subprocess.run(cmd_audio, check=True)
    total_audio_dur = get_audio_duration(combined_audio)
    print(f"✅ Combined Audio Created: {combined_audio} (Duration: {total_audio_dur:.2f}s, with 5.0s pause between parts)")

    # Collect images
    image_files = sorted(glob.glob(os.path.join(keyframes_dir, "*.jpg"))) + sorted(glob.glob(os.path.join(keyframes_dir, "*.png")))
    if not image_files:
        print("[Error] No keyframe images found in keyframes directory. Cannot assemble.")
        sys.exit(1)

    num_images = len(image_files)
    image_duration = total_audio_dur / num_images if num_images > 0 else 5.0
    print(f"  └─ Total Images: {num_images}, Duration per Image: {image_duration:.2f}s")

    # Filter graph for Ken Burns zoompan effect
    filter_complex = []
    inputs = []
    
    for idx, img in enumerate(image_files):
        inputs.extend(["-loop", "1", "-t", str(image_duration), "-i", img])
        if idx % 2 == 0:
            zoom_expr = f"zoompan=z='min(zoom+0.0015,1.25)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(image_duration*25)}:s=1920x1080"
        else:
            zoom_expr = f"zoompan=z='max(1.25-0.0015*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(image_duration*25)}:s=1920x1080"
        filter_complex.append(f"[{idx}:v]{zoom_expr}[v{idx}]")

    concat_inputs = "".join([f"[v{i}]" for i in range(num_images)])
    filter_complex.append(f"{concat_inputs}concat=n={num_images}:v=1:a=0[vfinal]")

    # Run FFmpeg Video Assembly
    cmd_video = ["ffmpeg", "-y"] + inputs + [
        "-i", combined_audio,
        "-filter_complex", ";".join(filter_complex),
        "-map", "[vfinal]", "-map", f"{len(image_files)}:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        output_mp4_path
    ]

    print("🚀 Rendering Master Video with Ken Burns effect...")
    subprocess.run(cmd_video, check=True)
    print(f"🎉 Master Video Rendered Successfully: {output_mp4_path}")

    # GK7 Quality Check
    video_dur = get_audio_duration(output_mp4_path)
    if video_dur > 0:
        print(f"✅ Gatekeeper GK7 QC Passed! Final Video Duration: {video_dur:.2f}s")
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
    else:
        print(f"⛔ Gatekeeper GK7 QC Failed for {output_mp4_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ken Burns Video Assembly for HistorySnooze")
    parser.add_argument("--project_dir", required=True, help="Project directory path")
    parser.add_argument("--output_mp4", required=True, help="Target output MP4 file path")
    args = parser.parse_args()

    build_kenburns_video(args.project_dir, args.output_mp4)
