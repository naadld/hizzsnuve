import os
import sys
import json
import re
import time
import argparse
import requests
from paced_scripting_engine import call_gemini_api

ILLUMINATED_STYLE_SUFFIX = "— late-15th-century illuminated manuscript style painting, tempera and shell-gold, flat medieval perspective, fine brown-ink outlines, full-bleed edge-to-edge painting extending to all four edges of the 16:9 canvas, zero margins, no outer paper, no parchment border, no decorative frame, no page border, wide cinematic 16:9 composition, ultra-high-resolution (4K)"

def generate_beats_for_part_1(character_name, script_text):
    """
    Part 1 Rules:
    - Image 1 (Cover): From beginning up to the paragraph containing "dim the light(s)"
    - Images 2, 3, 4: 3 static images for remaining text
    Total: 4 images for Part 1.
    Style: Borderless Late 15th-Century Illuminated Manuscript Miniature.
    """
    paragraphs = [p.strip() for p in script_text.split('\n\n') if p.strip()]
    
    dim_light_p_idx = 0
    for idx, p in enumerate(paragraphs):
        if "dim the light" in p.lower() or "dim the lights" in p.lower():
            dim_light_p_idx = idx
            break
            
    cover_text = "\n".join(paragraphs[:dim_light_p_idx + 1])
    remaining_paragraphs = paragraphs[dim_light_p_idx + 1:]
    remaining_text = "\n".join(remaining_paragraphs)

    system_prompt = f"""
You are an expert visual director creating Illuminated Manuscript Miniature style prompts for Google ImageFX.
Create 4 beats for Part 1:
- Beat 1 (Cover Art): Uses the character cover concept.
- Beats 2, 3, 4: Capture key visual moments in the remaining story text.

PROMPT FORMULA (MUST FOLLOW FOR EVERY BEAT):
"[Core scene description, key characters & actions, setting, mood, color accents] {ILLUMINATED_STYLE_SUFFIX}"

CRITICAL RULE:
Ensure the prompt includes "borderless full-bleed edge-to-edge artwork, no frame, no borders, no page margins" to prevent any decorative frames or page borders from appearing.

Format output strictly as JSON array of 4 beat objects:
[
  {{
    "beat_id": "P01_B01",
    "section": "Cover Art",
    "text_segment": "Summary of segment 1",
    "image_type": "cover",
    "prompt": "Grand historical portrait of {character_name} in regal medieval attire, serene atmosphere, rich crimson and gold accents {ILLUMINATED_STYLE_SUFFIX}"
  }},
  ...
]
"""
    user_prompt = f"""
Character: {character_name}
Part 1 Cover Segment: "{cover_text[:500]}..."
Part 1 Remaining Story Segment: "{remaining_text[:1500]}..."

Generate exactly 4 beats JSON (1 cover beat + 3 story beats for remaining text).
Prompts must follow the Illuminated Manuscript Miniature formula in English with borderless edge-to-edge artwork.
"""
    raw = call_gemini_api(user_prompt, system_prompt)
    clean_json_str = re.sub(r'^```json\s*|^```\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
    try:
        beats = json.loads(clean_json_str)
        return beats
    except Exception as e:
        print(f"[Error] Failed to parse Part 1 Beats JSON: {e}")
        # Fallback 4 beats
        return [
            {"beat_id": "P01_B01", "image_type": "cover", "prompt": f"Iconic portrait of {character_name}, cover art, regal medieval posture {ILLUMINATED_STYLE_SUFFIX}"},
            {"beat_id": "P01_B02", "image_type": "story", "prompt": f"Early life scene of {character_name}, quiet castle courtyard, morning light {ILLUMINATED_STYLE_SUFFIX}"},
            {"beat_id": "P01_B03", "image_type": "story", "prompt": f"Historical setting of {character_name}, medieval hall with banners {ILLUMINATED_STYLE_SUFFIX}"},
            {"beat_id": "P01_B04", "image_type": "story", "prompt": f"Atmospheric journey scene of {character_name}, twilight landscape {ILLUMINATED_STYLE_SUFFIX}"}
        ]

def generate_beats_for_middle_parts(character_name, part_num, script_text, num_images=4):
    """
    Part 2 to 14 Rules:
    - 4 to 5 static images per Part.
    - Style: Borderless Late 15th-Century Illuminated Manuscript Miniature.
    """
    system_prompt = f"""
You are a visual director creating Illuminated Manuscript Miniature prompts for Google ImageFX.
For Part {part_num}, generate exactly {num_images} distinct beats that cover the entire script content from beginning to end.

PROMPT FORMULA (MUST FOLLOW FOR EVERY BEAT):
"[Core scene description, key characters & actions, setting, mood, color accents] {ILLUMINATED_STYLE_SUFFIX}"

CRITICAL RULE:
Ensure the prompt includes "borderless full-bleed edge-to-edge artwork, no frame, no borders, no page margins" to prevent any decorative frames or page borders from appearing.

Format output strictly as JSON array of {num_images} objects:
[
  {{
    "beat_id": "P{part_num:02d}_B01",
    "image_type": "story",
    "text_segment": "Segment summary",
    "prompt": "Detailed medieval scene description {ILLUMINATED_STYLE_SUFFIX}"
  }},
  ...
]
"""
    user_prompt = f"""
Character: {character_name}
Part {part_num} Voiceover Script:
"{script_text[:2000]}..."

Generate exactly {num_images} beats covering all major narrative sections of Part {part_num}.
Follow the Illuminated Manuscript Miniature formula in English with borderless edge-to-edge artwork.
"""
    raw = call_gemini_api(user_prompt, system_prompt)
    clean_json_str = re.sub(r'^```json\s*|^```\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
    try:
        beats = json.loads(clean_json_str)
        return beats
    except Exception as e:
        print(f"[Error] Failed to parse Part {part_num} Beats JSON: {e}")
        return [
            {"beat_id": f"P{part_num:02d}_B{b:02d}", "image_type": "story", "prompt": f"Medieval narrative scene {b} of {character_name} in Part {part_num} {ILLUMINATED_STYLE_SUFFIX}"}
            for b in range(1, num_images + 1)
        ]

def generate_beats_for_part_15(character_name, script_text):
    """
    Part 15 Rules:
    - Maximum 3 static images:
      - Image 1 & 2: Describing final climax & resolution of the script.
      - Image 3: Summary variant image of historical character (artistic variant of cover).
    Style: Borderless Late 15th-Century Illuminated Manuscript Miniature.
    """
    system_prompt = f"""
You are a visual director creating Illuminated Manuscript Miniature prompts for Google ImageFX for Part 15 (Final Part).
Generate EXACTLY 3 beats:
- Beat 1: Climax moment of final part.
- Beat 2: Resolution / Legacy reflection moment.
- Beat 3 (Summary Variant): Master artistic summary portrait of the historical character (a grand variant of the cover image summarizing their eternal legacy).

PROMPT FORMULA (MUST FOLLOW FOR EVERY BEAT):
"[Core scene description, key characters & actions, setting, mood, color accents] {ILLUMINATED_STYLE_SUFFIX}"

CRITICAL RULE:
Ensure the prompt includes "borderless full-bleed edge-to-edge artwork, no frame, no borders, no page margins" to prevent any decorative frames or page borders from appearing.

Format output strictly as JSON array of 3 objects:
[
  {{
    "beat_id": "P15_B01",
    "image_type": "story_climax",
    "prompt": "Climax scene description {ILLUMINATED_STYLE_SUFFIX}"
  }},
  {{
    "beat_id": "P15_B02",
    "image_type": "story_resolution",
    "prompt": "Resolution scene description {ILLUMINATED_STYLE_SUFFIX}"
  }},
  {{
    "beat_id": "P15_B03",
    "image_type": "summary_variant",
    "prompt": "Master summary portrait of {character_name}, iconic legacy artwork {ILLUMINATED_STYLE_SUFFIX}"
  }}
]
"""
    user_prompt = f"""
Character: {character_name}
Part 15 Voiceover Script:
"{script_text[:2000]}..."

Generate exactly 3 beats as specified above (2 story climax/resolution beats + 1 summary variant portrait beat).
Follow the Illuminated Manuscript Miniature formula in English with borderless edge-to-edge artwork.
"""
    raw = call_gemini_api(user_prompt, system_prompt)
    clean_json_str = re.sub(r'^```json\s*|^```\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
    try:
        beats = json.loads(clean_json_str)
        return beats
    except Exception as e:
        print(f"[Error] Failed to parse Part 15 Beats JSON: {e}")
        return [
            {"beat_id": "P15_B01", "image_type": "story_climax", "prompt": f"Final climax scene of {character_name} {ILLUMINATED_STYLE_SUFFIX}"},
            {"beat_id": "P15_B02", "image_type": "story_resolution", "prompt": f"Legacy reflection scene of {character_name} {ILLUMINATED_STYLE_SUFFIX}"},
            {"beat_id": "P15_B03", "image_type": "summary_variant", "prompt": f"Master grand summary portrait variant of {character_name} {ILLUMINATED_STYLE_SUFFIX}"}
        ]

def run_beats_allocator_pipeline(character_name, project_dir, delay_seconds=30):
    preprod_dir = os.path.join(project_dir, "01.Preproduction")
    os.makedirs(preprod_dir, exist_ok=True)
    
    try:
        from gdrive_utils import sync_project_from_gdrive, sync_project_to_gdrive
        sync_project_from_gdrive(character_name, project_dir)
    except Exception as ge:
        print(f"⚠️ GDrive Pull Notice: {ge}")

    if not os.path.exists(preprod_dir):
        print(f"[Error] Preproduction directory {preprod_dir} not found.")
        sys.exit(1)

    print(f"\n--- Phase 3: Beats Prompt Allocator Pipeline for {character_name} (Illuminated Manuscript Style) ---")

    for part_num in range(1, 16):
        script_file = os.path.join(preprod_dir, f"Part_{part_num:02d}_Voiceover.txt")
        if not os.path.exists(script_file):
            print(f"[Warning] Script file {script_file} missing. Skipping.")
            continue

        with open(script_file, "r", encoding="utf-8") as f:
            script_text = f.read()

        if part_num == 1:
            beats = generate_beats_for_part_1(character_name, script_text)
        elif part_num == 15:
            beats = generate_beats_for_part_15(character_name, script_text)
        else:
            # Alternate between 4 and 5 images for parts 2-14
            num_imgs = 4 if part_num % 2 == 0 else 5
            beats = generate_beats_for_middle_parts(character_name, part_num, script_text, num_images=num_imgs)

        beats_file = os.path.join(preprod_dir, f"Part_{part_num:02d}_beats.json")
        with open(beats_file, "w", encoding="utf-8") as f:
            json.dump({"part_num": part_num, "total_beats": len(beats), "beats": beats}, f, indent=2, ensure_ascii=False)

        print(f"  └─ Saved Part {part_num:02d} ({len(beats)} beats) -> {beats_file}")

        if delay_seconds > 0:
            time.sleep(delay_seconds)

    combined_dir = os.path.join(project_dir, "02.Media Generation", "combined")
    os.makedirs(combined_dir, exist_ok=True)
    all_raw_prompts = []

    for part_num in range(1, 16):
        beats_file = os.path.join(preprod_dir, f"Part_{part_num:02d}_beats.json")
        if os.path.exists(beats_file):
            try:
                with open(beats_file, "r", encoding="utf-8") as f:
                    b_data = json.load(f)
                    for b in b_data.get("beats", []):
                        beat_id = b.get("beat_id", f"P{part_num:02d}_B01")
                        p_text = b.get("prompt", "").strip()
                        if p_text:
                            # Clean headings/bullets and remove newlines so it's strictly 1 line
                            clean_p = re.sub(r'^\s*[\-\*\d\.\#]+\s*', '', p_text)
                            clean_p = re.sub(r'\s+', ' ', clean_p).strip()
                            all_raw_prompts.append(f"beat_{beat_id}.jpg: {clean_p}")
            except Exception as ex:
                print(f"⚠️ Warning reading prompts for Part {part_num}: {ex}")

    combined_prompts_file = os.path.join(combined_dir, "combined_imageprompts.txt")
    with open(combined_prompts_file, "w", encoding="utf-8") as f:
        f.write("\n".join(all_raw_prompts))
    print(f"✅ Saved {len(all_raw_prompts)} Combined Image Prompts to {combined_prompts_file}")

    try:
        from gdrive_utils import sync_project_to_gdrive
        sync_project_to_gdrive(character_name, project_dir)
    except Exception as ge:
        print(f"⚠️ GDrive Sync Notice: {ge}")

    print(f"\n🎉 Completed Beats Allocation for {character_name}!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Beats Prompt Allocator for HistorySnooze (Illuminated Manuscript Miniature)")
    parser.add_argument("--character", required=True, help="Name of historical character")
    parser.add_argument("--project_dir", required=True, help="Project directory path")
    parser.add_argument("--delay", type=int, default=30, help="Delay between parts in seconds")
    args = parser.parse_args()

    run_beats_allocator_pipeline(args.character, args.project_dir, args.delay)
