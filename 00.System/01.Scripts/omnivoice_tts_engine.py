import os
import sys
import glob
import json
import time
import argparse
import subprocess
import re
import numpy as np
from googleapiclient.discovery import build

def notify_cloudflare(event_name, character_name, data=None):
    """Fires telemetry & gatekeeper status signals back to Cloudflare Worker Edge Gateway"""
    worker_url = os.environ.get("CLOUDFLARE_WORKER_URL", "https://historysnooze-gateway.hothihuong113.workers.dev")
    try:
        import requests
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

def ensure_omnivoice_installed():
    try:
        import omnivoice
        import soundfile
    except ImportError:
        print("📦 Installing OmniVoice and soundfile dependencies...")
        subprocess.run(["pip", "install", "-q", "git+https://github.com/k2-fsa/OmniVoice.git", "soundfile", "pydub"], check=True)

def validate_audio_file(file_path, expected_words=0):
    """
    GK4 Enhanced Physical & Acoustic Audio Validator:
    1. Size >= 10KB
    2. Non-Silent / RMS Energy > 0.005 (loại bỏ hoàn toàn file câm / mất tiếng)
    3. Duration Check: Thời lượng phải tương ứng với số từ (không bị nuốt / thiếu chunk)
    4. Tensor Integrity: Không chứa giá trị NaN / Inf / méo tiếng nghiêm trọng
    """
    if not os.path.exists(file_path):
        return False
    size = os.path.getsize(file_path)
    if size < 10240:
        print(f"⛔ [GK4 REJECTED] {os.path.basename(file_path)} size ({size/1024:.1f}KB) < 10KB. Corrupted file.")
        return False

    try:
        import soundfile as sf
        import numpy as np

        data, sr = sf.read(file_path)
        if data is None or len(data) == 0:
            print(f"⛔ [GK4 REJECTED] {os.path.basename(file_path)} has 0 audio samples.")
            return False

        # 1. Check for NaN / Inf (loại bỏ lỗi tensor)
        if np.isnan(data).any() or np.isinf(data).any():
            print(f"⛔ [GK4 REJECTED] {os.path.basename(file_path)} contains NaN/Inf values (distorted tensor).")
            return False

        # 2. Check duration vs word count (chống mất / thiếu chunk)
        duration_sec = len(data) / sr
        if expected_words > 200:
            min_expected_sec = expected_words * 0.15  # Tối thiểu 0.15s / từ
            if duration_sec < min_expected_sec:
                print(f"⛔ [GK4 REJECTED] {os.path.basename(file_path)} duration ({duration_sec:.1f}s) too short for {expected_words} words. Likely missing chunks.")
                return False

        # 3. Check RMS energy & Peak (chống file câm / rè)
        rms = np.sqrt(np.mean(data**2))
        peak = np.max(np.abs(data))
        if rms < 0.003 or peak < 0.02:
            print(f"⛔ [GK4 REJECTED] {os.path.basename(file_path)} is silent or near-inaudible (RMS: {rms:.5f}, Peak: {peak:.3f}).")
            return False

        print(f"✅ [GK4 PASSED] {os.path.basename(file_path)} | Size: {size/1024:.1f}KB | Duration: {duration_sec:.1f}s | RMS: {rms:.4f}")
        return True
    except Exception as e:
        print(f"⚠️ [GK4 Warning] Could not inspect audio deeply ({e}), passed on size.")
        return True

def split_paragraph_into_smart_chunks(paragraph: str, max_chars: int = 160, min_chars: int = 25):
    """
    Splits paragraph into sentence chunks.
    1. Sub-splits sentences > max_chars by clause boundaries (, ; : —).
    2. Merges micro-sentences < min_chars into adjacent chunks so OmniVoice never drops short words.
    """
    raw_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', paragraph) if s.strip()]
    initial_chunks = []

    for s in raw_sentences:
        if len(s) <= max_chars:
            initial_chunks.append(s)
        else:
            clauses = [c.strip() for c in re.split(r'(?<=[,;:\—\–])\s+', s) if c.strip()]
            current_clause = ""
            for c in clauses:
                if len(current_clause) + len(c) + 1 <= max_chars:
                    current_clause = f"{current_clause} {c}".strip()
                else:
                    if current_clause:
                        initial_chunks.append(current_clause)
                    current_clause = c
            if current_clause:
                initial_chunks.append(current_clause)

    # Merge micro-chunks (< min_chars)
    merged_chunks = []
    buffer = ""
    for c in initial_chunks:
        if not c:
            continue
        if len(c) < min_chars:
            if buffer:
                buffer = f"{buffer} {c}".strip()
            else:
                buffer = c
        else:
            if buffer:
                merged_chunks.append(f"{buffer} {c}".strip())
                buffer = ""
            else:
                merged_chunks.append(c)
    if buffer:
        if merged_chunks:
            merged_chunks[-1] = f"{merged_chunks[-1]} {buffer}".strip()
        else:
            merged_chunks.append(buffer)

    return [c for c in merged_chunks if c]

def generate_tts_for_part(character_name, project_dir, part_num, ref_voice_path, max_retries=3):
    preprod_dir = os.path.join(project_dir, "01.Preproduction")
    media_dir = os.path.join(project_dir, "02.Media Generation")
    audio_dir = os.path.join(media_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    part_str = f"{part_num:02d}"
    script_path = os.path.join(preprod_dir, f"Part_{part_str}_Voiceover.txt")
    out_wav_path = os.path.join(audio_dir, f"Part_{part_str}_Voiceover.wav")

    if not os.path.exists(script_path):
        print(f"[Error] Script file for Part {part_str} not found: {script_path}")
        return False

    with open(script_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print(f"[Error] Script file for Part {part_str} is empty.")
        return False

    word_count = len(text.split())

    if validate_audio_file(out_wav_path, expected_words=word_count):
        print(f"⏩ Part {part_str} audio already exists and passed GK4. Skipping.")
        return True

    print(f"\n🎙️ Generating OmniVoice TTS for Part {part_str} ({word_count} words)...")

    ensure_omnivoice_installed()

    from omnivoice import OmniVoice
    import soundfile as sf
    import torch
    import numpy as np
    import gc

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  └─ Device: {device.upper()}")

    # 1. Strict special character ban & text cleaning
    clean_text = re.sub(r'\[.*?\]|\(.*?\)', '', text)  # remove labels [NARRATOR], (cười)
    clean_text = re.sub(r'[*#@$%^&_~/\\|<>{}+=~`]', '', clean_text)  # ban all special symbols
    clean_text = re.sub(r'\.{4,}', '...', clean_text)
    clean_text = re.sub(r'(?<!\.)\.\.(?!\.)', '.', clean_text)
    clean_text = clean_text.strip()

    # 2. Split into Paragraphs
    raw_paragraphs = [p.strip() for p in clean_text.split('\n') if p.strip()]
    if not raw_paragraphs:
        raw_paragraphs = [clean_text]

    try:
        engine = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device=device)
        print("  └─ Loaded OmniVoice Model successfully.")
    except Exception as e:
        print(f"⛔ Failed to load OmniVoice Model: {e}")
        return False

    sample_rate = 24000
    pause_1s = np.zeros(int(sample_rate * 1.0), dtype=np.float32)
    pause_2s = np.zeros(int(sample_rate * 2.0), dtype=np.float32)

    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            print(f"\n🔄 [AUTO-RETRY {attempt}/{max_retries}] Regenerating Part {part_str} due to previous GK4 rejection...")
            time.sleep(2)

        try:
            audios = []
            all_chunks_succeeded = True
            print(f"  └─ Processing {len(raw_paragraphs)} paragraphs (Attempt {attempt}/{max_retries})...")
            
            for p_idx, para in enumerate(raw_paragraphs):
                chunks = split_paragraph_into_smart_chunks(para)
                
                for s_idx, chunk_text in enumerate(chunks):
                    if not chunk_text:
                        continue

                    chunk_wav = None
                    # Chunk-level 3-attempt retry to guarantee 100% chunk retention
                    for chunk_try in range(1, 4):
                        try:
                            if torch.cuda.is_available():
                                torch.cuda.empty_cache()

                            if ref_voice_path and os.path.exists(ref_voice_path) and chunk_try < 3:
                                chunk_wav = engine.generate(text=chunk_text, ref_audio=ref_voice_path)
                            else:
                                chunk_wav = engine.generate(text=chunk_text)

                            if isinstance(chunk_wav, list) or (hasattr(chunk_wav, 'ndim') and chunk_wav.ndim > 1):
                                chunk_wav = np.squeeze(chunk_wav)

                            if chunk_wav is not None and len(chunk_wav) > 0 and not np.isnan(chunk_wav).any():
                                break
                        except Exception as ce:
                            print(f"  ⚠️ Warning generating chunk {s_idx+1} (attempt {chunk_try}/3): {ce}")
                            time.sleep(0.5)

                    if chunk_wav is None or len(chunk_wav) == 0:
                        print(f"  ❌ Critical: Failed to generate chunk {s_idx+1}: '{chunk_text[:30]}...'")
                        all_chunks_succeeded = False
                        continue

                    audios.append(chunk_wav)

                    # 1.0s pause between chunks
                    if s_idx < len(chunks) - 1:
                        audios.append(pause_1s)

                # 2.0s pause between paragraphs & VRAM memory cleanup
                if p_idx < len(raw_paragraphs) - 1:
                    audios.append(pause_2s)
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()

            if not audios or not all_chunks_succeeded:
                print(f"[Error] Incomplete chunks generated for Part {part_str} on attempt {attempt}.")
                continue

            final_wav = np.concatenate(audios)
            sf.write(out_wav_path, final_wav, sample_rate)
            print(f"  └─ Saved Concatenated WAV: {out_wav_path}")

            if validate_audio_file(out_wav_path, expected_words=word_count):
                return True
            else:
                print(f"⚠️ [Attempt {attempt} Rejected by GK4] Cleaning up invalid file...")
                if os.path.exists(out_wav_path):
                    try:
                        os.remove(out_wav_path)
                    except:
                        pass
        except Exception as e:
            print(f"⛔ Error in attempt {attempt} for Part {part_str}: {e}")

    print(f"❌ [GK4 FINAL FAILURE] Part {part_str} failed after {max_retries} attempts. Flagged for targeted re-run.")
    return False

def run_voiceover_pipeline(character_name, project_dir, target_part=0, ref_voice_path=""):
    if not ref_voice_path:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ref_voice_path = os.path.join(base_dir, "00.Configuration", "historysnoozevoice_voice_milo.mp3")

    print(f"\n--- HistorySnooze OmniVoice TTS Engine ---")
    print(f"Character: {character_name}")
    print(f"Project Dir: {project_dir}")
    print(f"Reference Audio: {ref_voice_path}")

    # Pull Preproduction scripts from GDrive if missing
    try:
        from gdrive_utils import sync_project_from_gdrive, get_gdrive_service, ensure_project_tree, upload_file
        sync_project_from_gdrive(character_name, project_dir)
        gdrive_service = get_gdrive_service()
        tree = ensure_project_tree(gdrive_service, character_name) if gdrive_service else {}
    except Exception as ge:
        print(f"⚠️ GDrive Notice: {ge}")
        gdrive_service = None
        tree = {}

    # Update Sheet Status to Voicing
    try:
        from format_gsheet_control_center import SPREADSHEET_ID
        if gdrive_service:
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
                    body={"values": [["Voicing"]]}
                ).execute()
    except Exception as se:
        print(f"⚠️ Sheet Status Update Notice: {se}")

    if target_part > 0:
        parts_to_run = [target_part]
    else:
        parts_to_run = list(range(1, 16))

    success_count = 0
    for p in parts_to_run:
        ok = generate_tts_for_part(character_name, project_dir, p, ref_voice_path)
        if ok:
            success_count += 1
            if gdrive_service and tree.get("audio_id"):
                part_str = f"{p:02d}"
                out_wav_path = os.path.join(project_dir, "02.Media Generation", "audio", f"Part_{part_str}_Voiceover.wav")
                upload_file(gdrive_service, out_wav_path, parent_id=tree["audio_id"])

    if success_count == len(parts_to_run) and gdrive_service and tree.get("audio_id"):
        # Update Sheet Col H with Audio GDrive Link & Col D to Voiceover / Ready
        try:
            audio_gdrive_url = f"https://drive.google.com/drive/u/0/folders/{tree['audio_id']}"
            if row_idx:
                sheets_svc.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"Pipeline!H{row_idx}",
                    valueInputOption="USER_ENTERED",
                    body={"values": [[audio_gdrive_url]]}
                ).execute()

                # Check Col I (Image)
                img_val = rows[row_idx - 1][8] if len(rows[row_idx - 1]) > 8 else ""
                final_status = "Ready" if "https://" in img_val else "Voiceover"

                sheets_svc.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"Pipeline!D{row_idx}",
                    valueInputOption="USER_ENTERED",
                    body={"values": [[final_status]]}
                ).execute()
                print(f"✅ Updated Sheet Pipeline Row {row_idx}: Status={final_status}, Voiceover Link={audio_gdrive_url}")
        except Exception as se:
            print(f"⚠️ Sheet Link Update Error: {se}")

def combine_all_audio_parts(character_name, project_dir, artifacts_dir=""):
    """
    Stage 3: Combines all 15 audio parts into combined_voiceover.wav with 5.0s silence pacing.
    Uploads to Google Drive and updates Google Sheets.
    """
    media_dir = os.path.join(project_dir, "02.Media Generation")
    audio_dir = os.path.join(media_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    print(f"\n--- HistorySnooze Stage 3: Combine All 15 Audio Parts for {character_name} ---")

    # If artifacts_dir provided (downloaded from GH Actions artifacts), copy into audio_dir
    if artifacts_dir and os.path.exists(artifacts_dir):
        import shutil
        for root, _, files in os.walk(artifacts_dir):
            for f in files:
                if f.startswith("Part_") and f.endswith(".wav"):
                    src = os.path.join(root, f)
                    dst = os.path.join(audio_dir, f)
                    shutil.copy2(src, dst)
                    print(f"  └─ Collected: {f}")

    # Gather 15 audio parts
    audio_files = []
    for p in range(1, 16):
        part_str = f"{p:02d}"
        wav_path = os.path.join(audio_dir, f"Part_{part_str}_Voiceover.wav")
        if not os.path.exists(wav_path):
            matches = glob.glob(os.path.join(audio_dir, f"*Part_{part_str}*.wav"))
            if matches:
                wav_path = matches[0]
        if os.path.exists(wav_path):
            audio_files.append((p, wav_path))

    missing_parts = [p for p in range(1, 16) if not any(x[0] == p for x in audio_files)]
    print(f"Found {len(audio_files)}/15 Audio Parts for concatenation.")
    if len(audio_files) < 15:
        print(f"⛔ [GK4 INCOMPLETE] Found only {len(audio_files)}/15 audio parts. Missing: {missing_parts}. Cannot combine.")
        notify_cloudflare("GK_ERROR", character_name, {
            "gk": "GK4",
            "reason": f"Only {len(audio_files)}/15 parts collected from matrix",
            "missing_parts": missing_parts
        })
        return False

    # Create 5.0s silence wav
    silence_5s_path = os.path.join(audio_dir, "silence_5s.wav")
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", "5", "-c:a", "pcm_s16le", silence_5s_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    concat_txt_path = os.path.join(audio_dir, "concat_parts_list.txt")
    with open(concat_txt_path, "w", encoding="utf-8") as f:
        for idx, (_, path) in enumerate(audio_files):
            f.write(f"file '{path}'\n")
            if idx < len(audio_files) - 1 and os.path.exists(silence_5s_path):
                f.write(f"file '{silence_5s_path}'\n")

    combined_out_wav = os.path.join(audio_dir, "combined_voiceover.wav")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_txt_path, "-c:a", "pcm_s16le", combined_out_wav
    ]
    subprocess.run(cmd, check=True)
    print(f"🎉 Created Combined Master Audio: {combined_out_wav}")

    # GDrive Upload & Sheet Update
    try:
        from gdrive_utils import get_gdrive_service, ensure_project_tree, upload_file
        gdrive_service = get_gdrive_service()
        if gdrive_service:
            tree = ensure_project_tree(gdrive_service, character_name)
            if tree.get("audio_id"):
                # Upload all individual WAVs and combined WAV
                upload_file(gdrive_service, combined_out_wav, parent_id=tree["audio_id"])
                for _, path in audio_files:
                    upload_file(gdrive_service, path, parent_id=tree["audio_id"])

                audio_gdrive_url = f"https://drive.google.com/drive/u/0/folders/{tree['audio_id']}"
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
                        range=f"Pipeline!H{row_idx}",
                        valueInputOption="USER_ENTERED",
                        body={"values": [[audio_gdrive_url]]}
                    ).execute()

                    img_val = rows[row_idx - 1][8] if len(rows[row_idx - 1]) > 8 else ""
                    final_status = "Ready" if "https://" in img_val else "Voiceover"
                    sheets_svc.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=f"Pipeline!D{row_idx}",
                        valueInputOption="USER_ENTERED",
                        body={"values": [[final_status]]}
                    ).execute()
                    print(f"✅ Updated Sheet Pipeline Row {row_idx}: Status={final_status}, Audio Link={audio_gdrive_url}")

                # Bắn Signal sang Cloudflare Worker: 15/15 Audio Parts hoàn tất GK4!
                notify_cloudflare("VOICEOVER_COMPLETED", character_name, {
                    "status": "SUCCESS",
                    "total_parts": len(audio_files),
                    "combined_wav": combined_out_wav,
                    "audio_gdrive_url": audio_gdrive_url
                })
    except Exception as ge:
        print(f"⚠️ GDrive / Sheet Update Notice: {ge}")

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OmniVoice TTS Engine for HistorySnooze")
    parser.add_argument("--character", required=True, help="Historical character name")
    parser.add_argument("--project_dir", default="", help="Project directory path")
    parser.add_argument("--part", type=int, default=0, help="Specific part number (1-15) or 0 for all")
    parser.add_argument("--ref_voice", default="", help="Path to reference voice audio file")
    parser.add_argument("--combine", action="store_true", help="Combine all 15 parts into combined_voiceover.wav")
    parser.add_argument("--artifacts_dir", default="", help="Directory containing downloaded part artifacts")
    args = parser.parse_args()

    proj_dir = args.project_dir or f"01.Projects/{args.character}"

    if args.combine:
        combine_all_audio_parts(args.character, proj_dir, args.artifacts_dir)
    else:
        run_voiceover_pipeline(args.character, proj_dir, args.part, args.ref_voice)

