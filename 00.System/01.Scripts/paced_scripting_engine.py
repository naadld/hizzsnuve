import os
import sys
import json
import time
import re
import random
import argparse
import requests

# Default configuration
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

# Key Rotation Pool
RAW_KEYS = [
    os.environ.get("GEMINI_KEY_1"),
    os.environ.get("GEMINI_KEY_2"),
    os.environ.get("GEMINI_KEY_3"),
    os.environ.get("GEMINI_KEY_4"),
    os.environ.get("GEMINI_KEY_5"),
    os.environ.get("GEMINI_KEY_6"),
    os.environ.get("GEMINI_API_KEY"),
]
API_KEYS = [k for k in RAW_KEYS if k and len(k.strip()) > 5]

if not API_KEYS:
    API_KEYS = [os.environ.get("GEMINI_API_KEY", "DUMMY_KEY")]

class GeminiKeyRotator:
    def __init__(self, keys):
        self.keys = keys
        self.current_idx = 0
        self.cooldowns = {}

    def get_key(self):
        now = time.time()
        for _ in range(len(self.keys)):
            key = self.keys[self.current_idx]
            self.current_idx = (self.current_idx + 1) % len(self.keys)
            if self.cooldowns.get(key, 0) < now:
                return key
        time.sleep(10)
        return random.choice(self.keys)

    def mark_cooldown(self, key, seconds=60):
        print(f"[KeyRotator] Key ending in ...{key[-4:]} hit limit. Cooldown {seconds}s.")
        self.cooldowns[key] = time.time() + seconds

rotator = GeminiKeyRotator(API_KEYS)

def fix_mojibake_and_encoding(text):
    if not text:
        return ""
    if 'â' in text or 'Ã' in text:
        try:
            text = text.encode('raw_unicode_escape').decode('utf-8')
        except Exception:
            pass
    replacements = [
        ('â€™', "'"), ('â€œ', '"'), ('â€ ', '"'), ('â€”', ' - '), ('â€“', ' - '),
        ('â€', ''), ('’', "'"), ('‘', "'"), ('“', '"'), ('”', '"'),
        ('—', ' - '), ('–', ' - '), ('…', '...'), ('..', '.')
    ]
    for bad, good in replacements:
        text = text.replace(bad, good)

    # Normalize dot patterns:
    # 1. 4 or more dots (...., .........) -> standard 3-dot ellipsis '...'
    text = re.sub(r'\.{4,}', '...', text)
    # 2. Exactly 2 dots (..) -> single dot '.'
    text = re.sub(r'(?<!\.)\.\.(?!\.)', '.', text)
    # 3. Clean spaces around dots and punctuation
    text = re.sub(r'\s+([,\.\?!;:])', r'\1', text)
    # 4. Ensure space after punctuation (unless end of text)
    text = re.sub(r'([,\.\?!;:])([^\s\d\.\?!;:\'\"])', r'\1 \2', text)
    # 5. Clean mixed punctuation artifacts (e.g. !.. -> !, ?.. -> ?)
    text = re.sub(r'([!\?])\.+', r'\1', text)
    text = re.sub(r',\.+', ',', text)

    text = re.sub(r' +', ' ', text)
    return text.strip()

def call_gemini_api(prompt, system_instruction="", retries=3):
    for attempt in range(retries):
        key = rotator.get_key()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{DEFAULT_MODEL}:generateContent?key={key}"
        
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_instruction}\n\n{prompt}"}]}
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 4096
            }
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=90)
            if resp.status_code == 200:
                data = resp.json()
                try:
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return fix_mojibake_and_encoding(text)
                except (KeyError, IndexError) as e:
                    print(f"[API Warning] Could not parse response structure: {e}")
            elif resp.status_code in (429, 503):
                rotator.mark_cooldown(key, seconds=60)
            else:
                print(f"[API Error] Status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"[API Exception] Attempt {attempt+1}: {e}")
            
        time.sleep(3)
    return ""

def generate_outline(character_name, target_title=""):
    print(f"\n--- Phase 1: Generating Outline for {character_name} ---")
    system_prompt = (
        "You are a master historical documentary scriptwriter for HistorySnooze channel. "
        "Create a comprehensive 3-Act story arc outline divided into exactly 15 Parts. "
        "Format output strictly as valid JSON without markdown wrapping."
    )
    user_prompt = f"""
Character: {character_name}
Target YouTube Title: {target_title or f"The Whispered Legacy of {character_name}"}

Respond in valid JSON format with this exact structure:
{{
  "character": "{character_name}",
  "title": "{target_title}",
  "acts": [
    {{"act": 1, "title": "Act I: Rise & Foundation", "parts": [1, 2, 3, 4, 5]}},
    {{"act": 2, "title": "Act II: Conflict & Trials", "parts": [6, 7, 8, 9, 10]}},
    {{"act": 3, "title": "Act III: Legacy & Reflection", "parts": [11, 12, 13, 14, 15]}}
  ],
  "parts": [
    {{
      "part_num": 1,
      "part_title": "Title of Part 1",
      "summary": "Detailed summary of historical events covered in Part 1."
    }}
  ]
}}
(Include all 15 parts in the parts array)
"""
    raw = call_gemini_api(user_prompt, system_prompt)
    clean_json_str = re.sub(r'^```json\s*|^```\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
    try:
        data = json.loads(clean_json_str)
        return data
    except Exception as e:
        print(f"[Error] Failed to parse Outline JSON: {e}\nRaw output:\n{raw[:500]}")
        return None

def generate_part_script(character_name, part_info, rolling_context="", delay_seconds=90):
    part_num = part_info["part_num"]
    part_title = part_info.get("part_title", f"Part {part_num}")
    summary = part_info.get("summary", "")

    print(f"\n[Phase 2] Generating Part {part_num}/15: '{part_title}' (Waiting {delay_seconds}s between calls)...")

    system_prompt = """
Bạn là nhà biên kịch lịch sử cho kênh ASMR HistorySnooze.
Nhiệm vụ của bạn là viết kịch bản đọc ASMR truyền cảm, chậm rãi, thư giãn về nhân vật lịch sử.

QUY TẮC BẮT BUỘC (GATEKEEPER 2):
1. ĐỘ DÀI: Tối thiểu 750 từ và tối đa 900 từ tiếng Việt.
2. NỘI DUNG: Ấm áp, ASMR sâu lắng, giàu tính điện ảnh và triết lý, có lồng ghép Fact/Debate/Joke hấp dẫn.
3. ÉP CHỮ SỐ THÀNH CHỮ: 100% chữ số phải đổi thành chữ (Ví dụ: "năm 1945" -> "năm một ngàn chín trăm bốn mươi lăm", "thế kỷ 18" -> "thế kỷ mười tám").
4. KHÔNG CÓ KÝ TỰ VIẾT TẮT HOẶC KÝ HIỆU: Viết hoàn toàn bằng từ ngữ phát âm chuẩn tiếng Việt.
5. ĐẶC BIỆT PART 1: Đoạn văn mở đầu của Part 1 PHẢI kết thúc bằng câu hoặc cụm từ "dim the light" (hoặc "dim the lights") để tạo hiệu ứng chuyển cảnh thư giãn.
6. LỜI ĐỌC THUẦN TÚY: KHÔNG DÙNG NHÃN NHƯ [NARRATOR], [MUSIC], (Sound effect), (end of script), wordcount notes... Chỉ viết đúng lời đọc truyền cảm.
"""

    context_prompt = f"NGỮ CẢNH NỐI TIẾP TỪ PART {part_num-1} (200 từ cuối Part trước):\n\"{rolling_context}\"\n\n" if rolling_context else ""

    user_prompt = f"""
Nhân vật: {character_name}
Phần: Part {part_num} - {part_title}
Mục tiêu nội dung Part {part_num}: {summary}

{context_prompt}
Hãy viết trọn vẹn kịch bản đọc Voiceover cho Part {part_num} (ĐÚNG 750-900 từ, 100% chữ số đổi thành chữ).
{"Đảm bảo đoạn đầu có câu 'dim the light' để bắt đầu đi vào giấc ngủ." if part_num == 1 else "Bắt đầu nối tiếp tự nhiên ngay sau ngữ cảnh Part trước, không lặp lại lời giới thiệu."}
"""

    script_text = call_gemini_api(user_prompt, system_prompt)
    script_text = re.sub(r'\[.*?\]|\(.*?\)', '', script_text)
    script_text = re.sub(r'^\s*(NARRATOR|VOICEOVER|PART \d+|end of script|wordcount).*?:\s*', '', script_text, flags=re.MULTILINE | re.IGNORECASE)
    script_text = re.sub(r'(end of script|wordcount:?\s*\d+)', '', script_text, flags=re.IGNORECASE)
    
    if delay_seconds > 0:
        time.sleep(delay_seconds)
    return script_text.strip()

def run_paced_scripting_pipeline(character_name, output_dir, delay_seconds=90):
    os.makedirs(output_dir, exist_ok=True)
    preprod_dir = os.path.join(output_dir, "01.Preproduction")
    os.makedirs(preprod_dir, exist_ok=True)
    combined_dir = os.path.join(output_dir, "02.Media Generation", "combined")
    os.makedirs(combined_dir, exist_ok=True)

    outline_path = os.path.join(preprod_dir, "outline.json")
    outline_data = generate_outline(character_name)
    if not outline_data:
        print("[Error] Failed to generate outline. Aborting.")
        sys.exit(1)

    with open(outline_path, "w", encoding="utf-8") as f:
        json.dump(outline_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved Outline to {outline_path}")

    rolling_context = ""
    total_words = 0
    all_part_scripts = []

    parts_list = outline_data.get("parts", [])
    if not parts_list:
        parts_list = [{"part_num": i, "part_title": f"Part {i}", "summary": f"Historical events part {i}"} for i in range(1, 16)]

    for part_info in parts_list:
        p_num = part_info["part_num"]
        script_text = generate_part_script(character_name, part_info, rolling_context, delay_seconds=delay_seconds)
        
        part_file = os.path.join(preprod_dir, f"Part_{p_num:02d}_Voiceover.txt")
        with open(part_file, "w", encoding="utf-8") as f:
            f.write(script_text)

        words_count = len(script_text.split())
        total_words += words_count
        print(f"  └─ Saved Part {p_num:02d} ({words_count} words) -> {part_file}")

        all_part_scripts.append(f"--- PART {p_num:02d}: {part_info.get('part_title', '')} ---\n\n{script_text}")

        words = script_text.split()
        rolling_context = " ".join(words[-200:]) if len(words) > 200 else script_text

    # Write combined voiceover script
    combined_voice_file = os.path.join(combined_dir, "combined_voiceover.txt")
    with open(combined_voice_file, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_part_scripts))
    print(f"✅ Saved Combined Voiceover Script to {combined_voice_file}")

    print(f"\n🎉 Completed Paced Scripting Pipeline for {character_name}! Total Words: {total_words}")
    
    try:
        from gdrive_utils import sync_project_to_gdrive
        sync_project_to_gdrive(character_name, output_dir)
    except Exception as ge:
        print(f"⚠️ GDrive Sync Notice: {ge}")

    return preprod_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paced Scripting Engine for HistorySnooze")
    parser.add_argument("--character", required=True, help="Name of historical character")
    parser.add_argument("--output_dir", required=True, help="Target project output directory")
    parser.add_argument("--delay", type=int, default=90, help="Delay between parts in seconds (default 90)")
    args = parser.parse_args()

    run_paced_scripting_pipeline(args.character, args.output_dir, args.delay)
