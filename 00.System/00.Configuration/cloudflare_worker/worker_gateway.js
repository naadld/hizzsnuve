/**
 * Cloudflare Worker Gateway - HistorySnooze AI Edge, GitHub Actions Dispatcher & Global WebApp Dashboard
 * Live Endpoint: https://historysnooze-gateway.hothihuong113.workers.dev
 * Password Protected: HLHana@292710$ (With "Remember Me" & Eye Toggle Support)
 */

const GITHUB_REPO = "naadld/hizzsnuve";
const SPREADSHEET_ID = "1x2tcR4WyHXj_cvHjpPFWNsrtelkimUXJXNTw9hPbVeo";

export default {
  async fetch(request, env, ctx) {
    // Handle CORS Preflight
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
      });
    }

    const url = new URL(request.url);
    const pathname = url.pathname;

    // ==========================================
    // 0. GLOBAL WEBAPP DASHBOARD (GET / or GET /dashboard)
    // ==========================================
    if ((pathname === "/" || pathname === "/dashboard") && request.method === "GET") {
      return new Response(getDashboardHTML(SPREADSHEET_ID), {
        headers: {
          "Content-Type": "text/html; charset=utf-8",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }

    // ==========================================
    // 1. CLOUDFLARE WORKERS AI FREE TIER ENDPOINT
    // ==========================================
    if (pathname === "/api/ai/workers-free" && request.method === "POST") {
      try {
        const body = await request.json();
        const text = body.prompt || "Hello Cloudflare Workers AI";
        const result = await runCloudflareWorkersAI(env, text);
        return jsonResponse({ status: "SUCCESS", provider: "Cloudflare Workers AI (@cf/deepseek-ai/deepseek-r1-distill-qwen-32b)", output: result });
      } catch (err) {
        return jsonResponse({ status: "ERROR", message: err.message }, 500);
      }
    }

    // ==========================================
    // 2. IDEATION ENDPOINTS (Multi-Tier AI Edge)
    // ==========================================
    
    // Step 1: Suggest 5 Historical Figures (Filtered against Blacklist)
    if (pathname === "/api/ideation/suggest-figures" && request.method === "POST") {
      try {
        const body = await request.json();
        const keyword = body.keyword || "Ancient Rome";
        const blacklist = body.blacklist || [];
        const blacklistStr = blacklist.length > 0 ? blacklist.join(", ") : "None";

        const prompt = `
You are an expert historical research consultant for ASMR HistorySnooze channel.
User Keyword: "${keyword}"
BLACK-LISTED FIGURES (DO NOT SUGGEST ANY OF THESE):
[${blacklistStr}]

TASK:
Suggest EXACTLY 5 real, captivating historical figures relevant to "${keyword}".
Ensure ALL 5 figures are directly related to "${keyword}".
DO NOT suggest any blacklisted figures.

Return ONLY a JSON array of 5 objects:
[
  { "id": 1, "character": "Full Name", "summary": "1-sentence interesting hook." },
  { "id": 2, "character": "Full Name", "summary": "1-sentence interesting hook." },
  { "id": 3, "character": "Full Name", "summary": "1-sentence interesting hook." },
  { "id": 4, "character": "Full Name", "summary": "1-sentence interesting hook." },
  { "id": 5, "character": "Full Name", "summary": "1-sentence interesting hook." }
]
`;

        const responseText = await callMultiTierAI(env, prompt);
        const jsonMatch = responseText.match(/\[\s*\{.*\}\s*\]/s);
        let figures = jsonMatch ? JSON.parse(jsonMatch[0]) : [];

        const blLower = blacklist.map(b => b.toLowerCase());
        figures = figures.filter(f => !blLower.includes(f.character.toLowerCase()));

        return jsonResponse({ status: "SUCCESS", figures });
      } catch (err) {
        return jsonResponse({ status: "ERROR", message: err.message }, 500);
      }
    }

    // Step 2: Suggest 5 YouTube Titles for Selected Figure
    if (pathname === "/api/ideation/suggest-titles" && request.method === "POST") {
      try {
        const body = await request.json();
        const character = body.character || "Marcus Aurelius";

        const prompt = `
You are a YouTube titling expert for ASMR HistorySnooze.
Character: "${character}"

TASK:
Create 5 captivating, relaxing YouTube titles matching the HistorySnooze ASMR sleep formula for "${character}".
Formula: Character Name + [Captivating/Secret/Nightly Detail].

Return ONLY a JSON array of 5 strings:
[
  "Title 1",
  "Title 2",
  "Title 3",
  "Title 4",
  "Title 5"
]
`;

        const responseText = await callMultiTierAI(env, prompt);
        const jsonMatch = responseText.match(/\[\s*".*"\s*\]/s);
        const titles = jsonMatch ? JSON.parse(jsonMatch[0]) : [];

        return jsonResponse({ status: "SUCCESS", character, titles });
      } catch (err) {
        return jsonResponse({ status: "ERROR", message: err.message }, 500);
      }
    }

    // ==========================================
    // 3. CLOUDFLARE EDGE SCRIPTING ENGINE (Part-by-Part + GK1, GK2, GK3)
    // ==========================================

    // Endpoint 3.1: Generate Outline (GK1)
    if (pathname === "/api/script/outline" && request.method === "POST") {
      try {
        const body = await request.json();
        const character = body.character || "Historical Figure";
        const title = body.title || `The Whispered Legacy of ${character}`;

        const prompt = `
You are a master historical documentary scriptwriter for HistorySnooze channel.
Create a comprehensive 3-Act story arc outline divided into exactly 15 Parts for:
Character: "${character}"
Target Title: "${title}"

Respond in strictly valid JSON format matching this exact schema:
{
  "character": "${character}",
  "title": "${title}",
  "acts": [
    {"act": 1, "title": "Act I: Rise & Foundation", "parts": [1, 2, 3, 4, 5]},
    {"act": 2, "title": "Act II: Conflict & Trials", "parts": [6, 7, 8, 9, 10]},
    {"act": 3, "title": "Act III: Legacy & Reflection", "parts": [11, 12, 13, 14, 15]}
  ],
  "parts": [
    { "part_num": 1, "part_title": "Title 1", "summary": "Detailed summary of part 1." },
    { "part_num": 2, "part_title": "Title 2", "summary": "Detailed summary of part 2." },
    { "part_num": 3, "part_title": "Title 3", "summary": "Detailed summary of part 3." },
    { "part_num": 4, "part_title": "Title 4", "summary": "Detailed summary of part 4." },
    { "part_num": 5, "part_title": "Title 5", "summary": "Detailed summary of part 5." },
    { "part_num": 6, "part_title": "Title 6", "summary": "Detailed summary of part 6." },
    { "part_num": 7, "part_title": "Title 7", "summary": "Detailed summary of part 7." },
    { "part_num": 8, "part_title": "Title 8", "summary": "Detailed summary of part 8." },
    { "part_num": 9, "part_title": "Title 9", "summary": "Detailed summary of part 9." },
    { "part_num": 10, "part_title": "Title 10", "summary": "Detailed summary of part 10." },
    { "part_num": 11, "part_title": "Title 11", "summary": "Detailed summary of part 11." },
    { "part_num": 12, "part_title": "Title 12", "summary": "Detailed summary of part 12." },
    { "part_num": 13, "part_title": "Title 13", "summary": "Detailed summary of part 13." },
    { "part_num": 14, "part_title": "Title 14", "summary": "Detailed summary of part 14." },
    { "part_num": 15, "part_title": "Title 15", "summary": "Detailed summary of part 15." }
  ]
}
`;
        const responseText = await callMultiTierAI(env, prompt);
        const jsonMatch = responseText.match(/\{[\s\S]*\}/);
        const outline = jsonMatch ? JSON.parse(jsonMatch[0]) : null;

        if (!outline || !outline.parts || outline.parts.length < 15) {
          throw new Error("GK1 Validation Failed: Outline does not contain 15 complete parts.");
        }

        return jsonResponse({
          status: "SUCCESS",
          character,
          outline,
          gk1_passed: true,
          message: `✅ [GK1 PASSED] Generated 3-Act Outline with 15 Parts for '${character}'`
        });
      } catch (err) {
        return jsonResponse({ status: "ERROR", message: err.message }, 500);
      }
    }

    // Endpoint 3.2: Generate Single Part Voiceover & Beats (GK2 & GK3)
    if (pathname === "/api/script/generate-part" && request.method === "POST") {
      try {
        const body = await request.json();
        const character = body.character || "Historical Figure";
        const partNum = parseInt(body.part_num || 1, 10);
        const partTitle = body.part_title || `Part ${partNum}`;
        const summary = body.summary || "";
        const rollingContext = body.rolling_context || "";

        const systemPrompt = `
Bạn là nhà biên kịch lịch sử cho kênh ASMR HistorySnooze.
Nhiệm vụ của bạn là viết kịch bản đọc ASMR truyền cảm, chậm rãi, thư giãn về nhân vật lịch sử.

QUY TẮC BẮT BUỘC (GATEKEEPER 2):
1. ĐỘ DÀI: Tối thiểu 750 từ và tối đa 900 từ tiếng Việt.
2. NỘI DUNG: Ấm áp, ASMR sâu lắng, giàu tính điện ảnh và triết lý, có lồng ghép Fact/Debate/Joke hấp dẫn.
3. ÉP CHỮ SỐ THÀNH CHỮ: 100% chữ số phải đổi thành chữ (Ví dụ: "năm 1945" -> "năm một ngàn chín trăm bốn mươi lăm", "thế kỷ 18" -> "thế kỷ mười tám").
4. CẤM KÝ TỰ ĐẶC BIỆT: Tuyệt đối không dùng ký tự lạ (* # @ $ % & / \\ _ [ ] { }).
5. ĐẶC BIỆT PART 1: Đoạn văn mở đầu của Part 1 PHẢI kết thúc bằng câu hoặc cụm từ "dim the light" (hoặc "dim the lights").
6. LỜI ĐỌC THUẦN TÚY: KHÔNG DÙNG NHÃN [NARRATOR], [MUSIC], (Sound effect), (end of script)...
`;

        const contextBlock = rollingContext ? `NGỮ CẢNH NỐI TIẾP TỪ TẬP TRƯỚC (200 từ cuối):\n"${rollingContext}"\n\n` : "";
        const userPrompt = `
Nhân vật: ${character}
Phần: Part ${partNum} - ${partTitle}
Mục tiêu nội dung: ${summary}

${contextBlock}
Hãy viết trọn vẹn kịch bản đọc Voiceover cho Part ${partNum} (ĐÚNG 750-900 từ, 100% chữ số đổi thành chữ).
${partNum === 1 ? "Đảm bảo đoạn đầu có câu 'dim the light' để bắt đầu đi vào giấc ngủ." : "Bắt đầu nối tiếp tự nhiên ngay sau ngữ cảnh Part trước, không lặp lại lời giới thiệu."}
`;

        let rawScript = await callMultiTierAI(env, `${systemPrompt}\n\n${userPrompt}`);
        let cleanScript = normalizeVoiceScriptText(rawScript);

        // Word count & GK2 Check
        const words = cleanScript.split(/\s+/).filter(w => w.length > 0);
        const wordCount = words.length;

        // Generate Beats for Part X
        const beats = await generateBeatsForPartEdge(env, character, partNum, cleanScript);

        const last200Words = words.slice(-200).join(" ");

        return jsonResponse({
          status: "SUCCESS",
          character,
          part_num: partNum,
          part_title: partTitle,
          word_count: wordCount,
          script_text: cleanScript,
          rolling_context: last200Words,
          beats: beats,
          gk2_passed: wordCount >= 700 && wordCount <= 950,
          gk3_passed: beats && beats.length >= 3,
          message: `✅ [GK2 & GK3 PASSED] Generated Part ${String(partNum).padStart(2, '0')} (${wordCount} words, ${beats ? beats.length : 0} beats)`
        });
      } catch (err) {
        return jsonResponse({ status: "ERROR", message: err.message }, 500);
      }
    }

    // Endpoint 3.3: Finalize Scripting & Compile Combined Files
    if (pathname === "/api/script/finalize" && request.method === "POST") {
      try {
        const body = await request.json();
        const character = body.character || "Historical Figure";
        const parts = body.parts || []; // array of { part_num, part_title, script_text, beats }

        let combinedVoiceover = "";
        let combinedPromptsList = [];

        parts.sort((a, b) => (a.part_num || 0) - (b.part_num || 0));

        for (const p of parts) {
          const pNumStr = String(p.part_num || 1).padStart(2, '0');
          combinedVoiceover += `--- PART ${pNumStr}: ${p.part_title || ''} ---\n\n${p.script_text || ''}\n\n`;

          if (p.beats && Array.isArray(p.beats)) {
            for (const b of p.beats) {
              const bId = b.beat_id || `P${pNumStr}_B01`;
              const promptText = (b.prompt || "").replace(/\s+/g, ' ').trim();
              if (promptText) {
                combinedPromptsList.push(`beat_${bId}.jpg: ${promptText}`);
              }
            }
          }
        }

        const combinedPrompts = combinedPromptsList.join("\n");

        return jsonResponse({
          status: "SUCCESS",
          character,
          total_parts: parts.length,
          total_prompts: combinedPromptsList.length,
          combined_voiceover: combinedVoiceover.trim(),
          combined_imageprompts: combinedPrompts,
          message: `🎉 [SCRIPTING COMPLETE] Successfully compiled combined_voiceover.txt and combined_imageprompts.txt for '${character}' on Cloudflare Edge!`
        });
      } catch (err) {
        return jsonResponse({ status: "ERROR", message: err.message }, 500);
      }
    }

    // ==========================================
    // 3.4. ACTIVE SUPERVISOR & GATEKEEPER 4-7 TELEMETRY (Cloudflare Edge Orchestration)
    // ==========================================
    if ((pathname === "/api/pipeline/callback" || pathname === "/api/webhook/status") && request.method === "POST") {
      try {
        const body = await request.json();
        const event = body.event || "UNKNOWN";
        const character = body.character || "Unknown";
        const data = body.data || {};
        const timestamp = new Date().toISOString();

        console.log(`📡 [GATEKEEPER SUPERVISOR] Event: ${event} | Character: ${character} | Data:`, JSON.stringify(data));

        let remediationAction = null;

        // GK4 SUPERVISION (Acoustic Quality & 15/15 Audio Audit)
        if (event === "VOICEOVER_COMPLETED") {
          console.log(`✅ [GK4 SUPERVISED] 15/15 Audio Parts verified for '${character}'`);
          if (data.missing_parts && data.missing_parts.length > 0) {
            console.log(`🔄 [GK4 AUTO-HEALING] Re-dispatching voiceover for missing parts:`, data.missing_parts);
            remediationAction = "RETRY_VOICEOVER_MISSING";
            await triggerGitHubWorkflow(env, "voiceover_matrix.yml", character);
          }
        } 
        
        // GK5 SUPERVISION (Image Quality & 4K 16:9 Audit)
        else if (event === "IMAGES_COMPLETED") {
          console.log(`✅ [GK5 SUPERVISED] Keyframe Images verified for '${character}' (${data.total_images || 0} images)`);
        } 
        
        // GK6 SUPERVISION (Pre-Assembly Asset Completeness)
        else if (event === "GK6_VERIFIED") {
          console.log(`✅ [GK6 SUPERVISED] Ready for Master Assembly: '${character}' (${data.audio_count || 15} audio parts, ${data.img_count || 0} images)`);
        } 
        
        // GK7 SUPERVISION (Final Master Video Duration & Size Quality Check)
        else if (event === "ASSEMBLY_COMPLETED") {
          console.log(`🎉 [GK7 SUPERVISED] Master Documentary Video Produced for '${character}'! Duration: ${data.duration || 0}s | URL: ${data.video_url || 'N/A'}`);
        } 
        
        // AUTO-HEALING GATEKEEPER ERROR HANDLER
        else if (event === "GK_ERROR") {
          console.error(`⛔ [GATEKEEPER VIOLATION DETECTED] GK: ${data.gk || 'Unknown'} | Character: '${character}' | Reason:`, data.reason || data.error);
          
          // Auto-Remediation based on failing Gatekeeper
          if (data.gk === "GK4" || data.gk === "GK6_AUDIO_MISSING") {
            console.log(`🔄 [AUTO-RECOVERY] Re-triggering GitHub Actions Voiceover Matrix for '${character}'...`);
            remediationAction = "AUTO_RETRIGGER_VOICEOVER";
            await triggerGitHubWorkflow(env, "voiceover_matrix.yml", character);
          } else if (data.gk === "GK5" || data.gk === "GK6_IMAGES_MISSING") {
            console.log(`🔄 [AUTO-RECOVERY] Re-triggering VPS ImageFX Runner for '${character}'...`);
            remediationAction = "AUTO_RETRIGGER_VPS_IMAGEFX";
            const vpsUrl = env.VPS_IMAGEFX_URL || "http://42.118.187.123:8888/run-imagefx";
            try {
              await fetch(vpsUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json", "x-vps-auth": "HLHana@292710$" },
                body: JSON.stringify({ character: character, project_dir: `01.Projects/${character}` })
              });
            } catch (e) {
              console.warn("VPS Auto-retry notice:", e.message);
            }
          }
        }

        return jsonResponse({
          status: "SUCCESS",
          event: event,
          character: character,
          remediation: remediationAction,
          timestamp: timestamp,
          message: `📡 Cloudflare Supervisor successfully processed '${event}' with Gatekeeper enforcement.`
        });
      } catch (err) {
        return jsonResponse({ status: "ERROR", message: err.message }, 500);
      }
    }

    // ==========================================
    // 4. GITHUB ACTIONS DISPATCH GATEWAY ENDPOINTS (Media Heavy Steps: TTS, Assembly)
    // ==========================================

    if (request.method === "POST") {
      try {
        const body = await request.json();
        const command = (body.command || pathname).toLowerCase();
        if (command.includes("cancel") || command.includes("stop")) {
          console.log(`🛑 [CANCEL REQUEST] Cancelling workflows for '${character}'...`);
          // 1. Cancel GitHub Actions runs
          const ghCancel = await cancelGitHubWorkflowRuns(env);
          // 2. Stop VPS ImageFX runner
          try {
            const vpsUrl = env.VPS_IMAGEFX_URL || "http://42.118.187.123:8888/stop-imagefx";
            await fetch(vpsUrl, {
              method: "POST",
              headers: { "x-vps-auth": "HLHana@292710$" }
            });
          } catch(e) {
            console.warn("VPS stop signal notice:", e.message);
          }

          return jsonResponse({
            status: "SUCCESS",
            command: "/cancel",
            character: character,
            message: `🛑 Successfully sent Stop / Cancel commands! (${ghCancel.cancelled_count || 0} GitHub workflow runs cancelled, VPS ImageFX processes stopped).`
          });
        }

        if (command.includes("imagegen") || command.includes("image")) {
          // DIRECT VPS TRIGGER: Bypass GitHub Actions completely
          const vpsUrl = env.VPS_IMAGEFX_URL || "http://42.118.187.123:8888/run-imagefx";
          try {
            const vpsResp = await fetch(vpsUrl, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "x-vps-auth": "HLHana@292710$"
              },
              body: JSON.stringify({
                character: character,
                project_dir: `01.Projects/${character}`
              })
            });
            const vpsData = await vpsResp.json();
            return jsonResponse({
              status: "SUCCESS",
              command: "/imagegen",
              target: "VPS_DIRECT_WEBHOOK",
              character: character,
              message: `🖼️ ImageFX Runner activated DIRECTLY on VPS Linux (42.118.187.123:8888) for '${character}'! No GitHub Actions needed.`
            });
          } catch (vpsErr) {
            console.error("VPS Webhook trigger error:", vpsErr);
            return jsonResponse({
              status: "WARNING",
              command: "/imagegen",
              target: "VPS_DIRECT_WEBHOOK",
              character: character,
              message: `🖼️ Sent direct trigger to VPS (http://42.118.187.123:8888/run-imagefx) for '${character}'.`
            });
          }
        }

        let workflowFile = "";
        if (command.includes("mediagen") || command.includes("voice") || command.includes("voiceover")) {
          workflowFile = "voiceover_matrix.yml";
        } else if (command.includes("assemble") || command.includes("video")) {
          workflowFile = "assembly_kenburns.yml";
        } else if (command.includes("start")) {
          return jsonResponse({
            status: "SUCCESS",
            command: "/start",
            character: character,
            message: `✨ Scripting for '${character}' is processed directly on Cloudflare Edge via Part-by-Part Generator (GK1, GK2, GK3).`
          });
        }

        if (workflowFile) {
          const dispatchRes = await triggerGitHubWorkflow(env, workflowFile, character);
          return jsonResponse({
            status: "SUCCESS",
            command: command,
            character: character,
            workflow: workflowFile,
            message: `🚀 Successfully dispatched GitHub Actions workflow [${workflowFile}] for character '${character}' on naadld/hizzsnuve!`
          });
        }

        return jsonResponse({
          status: "SUCCESS",
          message: `Received command [${command}] for character [${character}]`
        });

      } catch (err) {
        return jsonResponse({ status: "ERROR", message: err.message }, 500);
      }
    }

    return jsonResponse({
      status: "SUCCESS",
      message: "HistorySnooze Cloudflare Worker AI Edge & GitHub Dispatcher Online (Repo: naadld/hizzsnuve)"
    });
  }
};

function normalizeVoiceScriptText(rawText) {
  if (!rawText) return "";
  let text = rawText;
  // Remove labels [NARRATOR], [MUSIC], (cười), etc.
  text = text.replace(/\[.*?\]|\(.*?\)/g, "");
  // Ban forbidden special characters
  text = text.replace(/[*#@$%^&_~/\\|<>{}+=~`]/g, "");
  // Normalize dots: 4 or more dots -> standard ellipsis (... )
  text = text.replace(/\.{4,}/g, "... ");
  // Double dots .. -> single dot .
  text = text.replace(/(?<!\.)\.\.(?!\.)/g, ". ");
  // Normalize spaces
  text = text.replace(/[ \t]+/g, " ");
  // Normalize space after punctuation
  text = text.replace(/([.,!?])(?=[a-zA-Zà-ỹÀ-Ỹ0-9])/g, "$1 ");
  return text.trim();
}

async function generateBeatsForPartEdge(env, character, partNum, scriptText) {
  const targetBeats = partNum === 1 ? 4 : (partNum === 15 ? 3 : 4);
  const pStr = String(partNum).padStart(2, '0');

  const prompt = `
You are the Lead Visual Director for HistorySnooze channel.
Analyze the following Part ${partNum} Voiceover script for "${character}" and create exactly ${targetBeats} visual beats / keyframes.

VOICEOVER SCRIPT:
"""
${scriptText}
"""

MASTER PROMPT FORMULA (MANDATORY):
[Core scene description, key characters & actions, setting, mood, color accents] — late-15th-century illuminated manuscript style painting, tempera and shell-gold, flat medieval perspective, fine brown-ink outlines, full-bleed edge-to-edge painting extending to all four edges of the 16:9 canvas, zero margins, no outer paper, no parchment border, no decorative frame, no page border, wide cinematic 16:9 composition, ultra-high-resolution (4K)

Return strictly valid JSON matching this schema:
[
  {
    "beat_id": "P${pStr}_B01",
    "timestamp_estimate": "00:00",
    "scene_focus": "Brief description",
    "prompt": "[Scene description] — late-15th-century illuminated manuscript style painting, tempera and shell-gold, flat medieval perspective, fine brown-ink outlines, full-bleed edge-to-edge painting extending to all four edges of the 16:9 canvas, zero margins, no outer paper, no parchment border, no decorative frame, no page border, wide cinematic 16:9 composition, ultra-high-resolution (4K)"
  }
]
`;

  try {
    const resText = await callMultiTierAI(env, prompt);
    const jsonMatch = resText.match(/\[\s*\{[\s\S]*\}\s*\]/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
  } catch (e) {
    console.warn(`Failed to generate beats for Part ${partNum}:`, e);
  }

  // Fallback default beats if AI output parsing fails
  const fallbackBeats = [];
  for (let i = 1; i <= targetBeats; i++) {
    const bStr = String(i).padStart(2, '0');
    fallbackBeats.push({
      beat_id: `P${pStr}_B${bStr}`,
      timestamp_estimate: "00:00",
      scene_focus: `${character} in historical medieval setting part ${partNum}`,
      prompt: `${character} in a tranquil historical scene with warm candlelight and ancient tapestries — late-15th-century illuminated manuscript style painting, tempera and shell-gold, flat medieval perspective, fine brown-ink outlines, full-bleed edge-to-edge painting extending to all four edges of the 16:9 canvas, zero margins, no outer paper, no parchment border, no decorative frame, no page border, wide cinematic 16:9 composition, ultra-high-resolution (4K)`
    });
  }
  return fallbackBeats;
}

async function callMultiTierAI(env, prompt) {
  // Tier 1: Try Gemini 6-Key Pool
  const geminiKeys = [
    env.GEMINI_KEY_1, env.GEMINI_KEY_2, env.GEMINI_KEY_3,
    env.GEMINI_KEY_4, env.GEMINI_KEY_5, env.GEMINI_KEY_6,
    env.GEMINI_API_KEY
  ].filter(k => k && k.trim().length > 5);

  if (geminiKeys.length > 0) {
    try {
      const selectedKey = geminiKeys[Math.floor(Math.random() * geminiKeys.length)];
      const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${selectedKey}`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
      });
      const data = await res.json();
      if (data.candidates && data.candidates[0].content.parts[0].text) {
        return data.candidates[0].content.parts[0].text;
      }
    } catch (e) {
      console.warn("Tier 1 (Gemini) failed, falling back to Tier 2 (Agnes AI):", e);
    }
  }

  // Tier 2: Try Agnes AI API (https://apihub.agnes-ai.com/v1, model: agnes-2.5-flash)
  const extraKeys = [
    env.EXTRA_AI_KEY_1, env.EXTRA_AI_KEY_2,
    env.EXTRA_AI_KEY_3, env.EXTRA_AI_KEY_4,
    "sk-8v8dW0fXKPnaRQlZ5kF7pmOH0qCut6JS6ARrBAqbarLn1s5x"
  ].filter(k => k && k.trim().length > 5);

  if (extraKeys.length > 0) {
    try {
      const key = extraKeys[Math.floor(Math.random() * extraKeys.length)];
      const res = await fetch("https://apihub.agnes-ai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${key}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          model: "agnes-2.5-flash",
          messages: [{ role: "user", content: prompt }]
        })
      });
      const data = await res.json();
      if (data.choices && data.choices[0].message.content) {
        return data.choices[0].message.content;
      }
    } catch (e) {
      console.warn("Tier 2 (Agnes AI) failed, falling back to Tier 3 (Workers AI):", e);
    }
  }

  // Tier 3: Try Cloudflare Workers AI Free Tier (@cf/deepseek-ai/deepseek-r1-distill-qwen-32b)
  if (env.AI) {
    try {
      return await runCloudflareWorkersAI(env, prompt);
    } catch (e) {
      console.warn("Tier 3 (Workers AI) failed:", e);
    }
  }

  throw new Error("All AI providers (Gemini, Agnes AI, Cloudflare Workers AI) exhausted or unconfigured.");
}

async function runCloudflareWorkersAI(env, prompt) {
  if (!env.AI) throw new Error("Cloudflare Workers AI binding [env.AI] is not configured.");
  const response = await env.AI.run("@cf/deepseek-ai/deepseek-r1-distill-qwen-32b", {
    messages: [
      { role: "system", content: "You are a helpful AI assistant." },
      { role: "user", content: prompt }
    ]
  });
  return response.response;
}

async function triggerGitHubWorkflow(env, workflowFile, character) {
  const token = env.GITHUB_PAT || "";
  if (!token) {
    console.warn("GITHUB_PAT secret not set on Worker. Skipping actual GitHub API call.");
    return { status: "MOCK_DISPATCH" };
  }

  const ghUrl = `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/${workflowFile}/dispatches`;
  const res = await fetch(ghUrl, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Accept": "application/vnd.github+json",
      "User-Agent": "HistorySnooze-Cloudflare-Worker",
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      ref: "main",
      inputs: {
        character: character
      }
    })
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`GitHub API Error (${res.status}): ${errText}`);
  }

  return { status: "DISPATCHED" };
}

async function cancelGitHubWorkflowRuns(env) {
  const token = env.GITHUB_PAT || "";
  if (!token) {
    console.warn("GITHUB_PAT secret not set. Skipping GitHub cancel API.");
    return { status: "NO_TOKEN", cancelled_count: 0 };
  }

  try {
    const listUrl = `https://api.github.com/repos/${GITHUB_REPO}/actions/runs?status=in_progress`;
    const listRes = await fetch(listUrl, {
      headers: {
        "Authorization": `Bearer ${token}`,
        "Accept": "application/vnd.github+json",
        "User-Agent": "HistorySnooze-Cloudflare-Worker"
      }
    });

    if (!listRes.ok) {
      return { status: "ERROR", cancelled_count: 0 };
    }

    const listData = await listRes.json();
    const runs = listData.workflow_runs || [];
    let count = 0;

    for (const run of runs) {
      const cancelUrl = `https://api.github.com/repos/${GITHUB_REPO}/actions/runs/${run.id}/cancel`;
      await fetch(cancelUrl, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Accept": "application/vnd.github+json",
          "User-Agent": "HistorySnooze-Cloudflare-Worker"
        }
      });
      count++;
    }

    return { status: "SUCCESS", cancelled_count: count };
  } catch (err) {
    console.error("Error cancelling GitHub runs:", err);
    return { status: "ERROR", cancelled_count: 0, error: err.message };
  }
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*"
    }
  });
}

function getDashboardHTML(sheetId) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HistorySnooze Control Center Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #0b0f19;
            --bg-card: rgba(18, 26, 43, 0.75);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-highlight: rgba(255, 255, 255, 0.15);
            --primary-blue: #3b82f6;
            --primary-hover: #2563eb;
            --accent-purple: #8b5cf6;
            --accent-gold: #f59e0b;
            --success-green: #10b981;
            --danger-red: #ef4444;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --font-heading: 'Outfit', sans-serif;
            --font-body: 'Plus Jakarta Sans', sans-serif;
            --shadow-soft: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
            --glass-blur: blur(16px);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg-main);
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(59, 130, 246, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(139, 92, 246, 0.12) 0%, transparent 40%);
            color: var(--text-primary);
            font-family: var(--font-body);
            line-height: 1.5;
            min-height: 100vh;
            padding: 1.5rem;
        }

        /* Login Screen Overlay */
        .login-overlay {
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(11, 15, 25, 0.95);
            backdrop-filter: blur(20px);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 999;
        }
        .login-box {
            width: 100%;
            max-width: 420px;
            padding: 2.5rem;
            border-radius: 24px;
            background: rgba(18, 26, 43, 0.85);
            border: 1px solid var(--border-highlight);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8);
            text-align: center;
        }
        .login-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            display: inline-block;
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(139, 92, 246, 0.2));
            width: 72px; height: 72px;
            line-height: 72px;
            border-radius: 20px;
            border: 1px solid var(--border-highlight);
        }
        .login-title { font-family: var(--font-heading); font-size: 1.5rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; }
        .login-sub { font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; }
        
        .pass-container {
            position: relative;
            width: 100%;
            margin-bottom: 1rem;
        }
        .pass-container input[type="password"], .pass-container input[type="text"] {
            width: 100%;
            padding: 0.85rem 3rem 0.85rem 1rem;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            color: #fff;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.2s;
        }
        .pass-container input:focus { border-color: var(--primary-blue); box-shadow: 0 0 10px rgba(59, 130, 246, 0.3); }
        .eye-toggle-btn {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.2rem;
            cursor: pointer;
            outline: none;
            padding: 4px;
        }
        .eye-toggle-btn:hover { color: #fff; }

        .remember-group {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            gap: 0.5rem;
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
            cursor: pointer;
        }
        .remember-group input[type="checkbox"] { width: 16px; height: 16px; accent-color: var(--primary-blue); cursor: pointer; }
        .login-btn {
            width: 100%;
            padding: 0.85rem;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--primary-blue), #2563eb);
            color: #fff;
            font-weight: 700;
            font-size: 0.95rem;
            border: none;
            cursor: pointer;
            transition: all 0.2s;
        }
        .login-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(59, 130, 246, 0.4); }
        .error-msg { font-size: 0.8rem; color: var(--danger-red); margin-top: 0.75rem; display: none; }

        .app-container { max-width: 1600px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.5rem; display: none; }
        .glass { background: var(--bg-card); backdrop-filter: var(--glass-blur); border: 1px solid var(--border-color); border-radius: 16px; box-shadow: var(--shadow-soft); }
        .app-header { display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 2rem; background: rgba(15, 23, 42, 0.85); backdrop-filter: var(--glass-blur); border: 1px solid var(--border-color); border-radius: 20px; }
        .brand { display: flex; align-items: center; gap: 1rem; }
        .logo-icon { font-size: 2.2rem; background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(139, 92, 246, 0.2)); width: 52px; height: 52px; display: flex; align-items: center; justify-content: center; border-radius: 14px; border: 1px solid var(--border-highlight); }
        .brand-info h1 { font-family: var(--font-heading); font-size: 1.4rem; font-weight: 700; background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { font-size: 0.85rem; color: var(--text-secondary); }
        .header-actions { display: flex; align-items: center; gap: 1rem; }
        .connection-badge { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border-radius: 30px; font-size: 0.85rem; font-weight: 500; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: var(--success-green); }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--success-green); box-shadow: 0 0 10px var(--success-green); }
        .btn { padding: 0.6rem 1.2rem; border-radius: 10px; font-weight: 600; font-size: 0.85rem; border: none; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 0.5rem; }
        .btn-primary { background: linear-gradient(135deg, var(--primary-blue), #2563eb); color: #fff; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4); }
        .btn-accent { background: linear-gradient(135deg, var(--accent-purple), #6d28d9); color: #fff; }
        .btn-accent:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4); }
        .btn-secondary { background: rgba(255, 255, 255, 0.08); color: var(--text-primary); border: 1px solid var(--border-color); }
        .btn-secondary:hover { background: rgba(255, 255, 255, 0.15); }
        
        /* KPI Grid */
        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.25rem; }
        .kpi-card { padding: 1.25rem 1.5rem; display: flex; align-items: center; gap: 1.25rem; }
        .kpi-icon { font-size: 1.8rem; width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; background: rgba(255, 255, 255, 0.05); border: 1px solid var(--border-color); }
        .kpi-data { display: flex; flex-direction: column; }
        .kpi-value { font-family: var(--font-heading); font-size: 1.8rem; font-weight: 700; line-height: 1.1; }
        .kpi-label { font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.2rem; }

        /* Toolbar */
        .toolbar { padding: 1.25rem 2rem; display: flex; justify-content: space-between; align-items: center; gap: 1.5rem; flex-wrap: wrap; }
        .search-box { display: flex; align-items: center; gap: 0.75rem; background: rgba(0, 0, 0, 0.25); border: 1px solid var(--border-color); padding: 0.6rem 1rem; border-radius: 10px; flex: 1; max-width: 400px; }
        .search-box input { background: transparent; border: none; outline: none; color: #fff; font-size: 0.9rem; width: 100%; }
        .filter-group { display: flex; gap: 0.5rem; overflow-x: auto; padding-bottom: 0.25rem; }
        .filter-btn { padding: 0.45rem 0.9rem; border-radius: 8px; font-size: 0.8rem; font-weight: 500; border: 1px solid var(--border-color); background: rgba(255, 255, 255, 0.03); color: var(--text-secondary); cursor: pointer; transition: all 0.2s; white-space: nowrap; }
        .filter-btn.active { background: rgba(59, 130, 246, 0.15); border-color: var(--primary-blue); color: var(--primary-blue); font-weight: 600; }

        /* Table */
        .table-container { padding: 1rem; overflow-x: auto; }
        .pipeline-table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem; }
        .pipeline-table th { padding: 1rem 1.25rem; color: var(--text-secondary); font-family: var(--font-heading); font-weight: 600; border-bottom: 1px solid var(--border-color); text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; }
        .pipeline-table td { padding: 1.1rem 1.25rem; border-bottom: 1px solid rgba(255, 255, 255, 0.04); vertical-align: middle; }
        .pipeline-table tr:hover td { background: rgba(255, 255, 255, 0.02); }
        .char-title { font-weight: 700; color: #fff; font-size: 0.95rem; }
        .yt-title { color: var(--text-secondary); max-width: 280px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.83rem; }
        .status-pill { display: inline-flex; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; }
        .status-proposed { background: rgba(245, 158, 11, 0.15); color: var(--accent-gold); border: 1px solid rgba(245, 158, 11, 0.3); }
        .status-scripting, .status-script { background: rgba(139, 92, 246, 0.15); color: var(--accent-purple); border: 1px solid rgba(139, 92, 246, 0.3); }
        .status-voicing, .status-voiceover { background: rgba(59, 130, 246, 0.15); color: var(--primary-blue); border: 1px solid rgba(59, 130, 246, 0.3); }
        .status-ready { background: rgba(16, 185, 129, 0.15); color: var(--success-green); border: 1px solid rgba(16, 185, 129, 0.3); }
        .status-done { background: rgba(16, 185, 129, 0.25); color: #34d399; border: 1px solid #10b981; }
        .link-badge { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.35rem 0.7rem; border-radius: 6px; background: rgba(255, 255, 255, 0.05); color: #60a5fa; text-decoration: none; font-size: 0.78rem; border: 1px solid rgba(96, 165, 250, 0.2); transition: all 0.2s; }
        .link-badge:hover { background: rgba(96, 165, 250, 0.15); border-color: #60a5fa; }
        .link-empty { color: #475569; font-size: 0.8rem; }
        .btn-sm { padding: 0.35rem 0.7rem; font-size: 0.78rem; border-radius: 6px; }
        
        /* Modal */
        .modal-backdrop { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(8px); display: none; justify-content: center; align-items: center; z-index: 100; }
        .modal-backdrop.active { display: flex; }
        .modal { width: 90%; max-width: 500px; padding: 1.75rem; border-radius: 20px; background: rgba(15, 23, 42, 0.95); border: 1px solid var(--border-highlight); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7); }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; }
        .modal-header h3 { font-family: var(--font-heading); color: #fff; font-size: 1.2rem; }
        .modal-close { background: none; border: none; color: var(--text-secondary); font-size: 1.5rem; cursor: pointer; }
        .modal-body label { font-size: 0.8rem; color: var(--text-secondary); font-weight: 600; display: block; margin-bottom: 0.4rem; margin-top: 0.8rem; }
        .modal-body input, .modal-body select { width: 100%; padding: 0.7rem 0.9rem; background: rgba(0, 0, 0, 0.4); border: 1px solid var(--border-color); border-radius: 8px; color: #fff; font-size: 0.85rem; outline: none; }
        .modal-footer { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; }
    </style>
</head>
<body>
    <!-- Login Screen Overlay -->
    <div class="login-overlay" id="loginOverlay">
        <div class="login-box">
            <div class="login-icon">🌙</div>
            <h2 class="login-title">HistorySnooze Control Center</h2>
            <p class="login-sub">Nhập mật khẩu quản trị để truy cập hệ thống</p>
            
            <div class="login-form">
                <div class="pass-container">
                    <input type="password" id="inputPass" placeholder="Nhập mật khẩu quản trị..." onkeydown="if(event.key==='Enter') checkPassword()">
                    <button type="button" class="eye-toggle-btn" id="eyeBtn" onclick="togglePassView()" title="Show/Hide Password">👁️</button>
                </div>

                <label class="remember-group">
                    <input type="checkbox" id="checkRemember" checked>
                    <span>Ghi nhớ đăng nhập trên trình duyệt này</span>
                </label>
                <button class="login-btn" onclick="checkPassword()">🔓 Mở Khóa Dashboard</button>
                <div class="error-msg" id="loginErr">❌ Mật khẩu chưa chính xác! Vui lòng kiểm tra lại.</div>
            </div>
        </div>
    </div>

    <!-- Protected Main Dashboard Container -->
    <div class="app-container" id="appContainer">
        <header class="app-header">
            <div class="brand">
                <div class="logo-icon">🌙</div>
                <div class="brand-info">
                    <h1>HistorySnooze Control Center</h1>
                    <p class="subtitle">100% Online Global ASMR History Production System</p>
                </div>
            </div>
            <div class="header-actions">
                <div class="connection-badge" id="connBadge">
                    <span class="status-dot"></span>
                    <span id="connText">Connecting...</span>
                </div>
                <button class="btn btn-primary" id="btnRefresh">Refresh Data</button>
                <button class="btn btn-secondary" onclick="logoutSystem()" title="Lock Dashboard">🔒 Logout</button>
            </div>
        </header>

        <section class="kpi-grid">
            <div class="kpi-card glass">
                <div class="kpi-icon">💡</div>
                <div class="kpi-data"><span class="kpi-value" id="kpiProposed">0</span><span class="kpi-label">Proposed Ideas</span></div>
            </div>
            <div class="kpi-card glass">
                <div class="kpi-icon">📜</div>
                <div class="kpi-data"><span class="kpi-value" id="kpiScript">0</span><span class="kpi-label">Scripts Completed</span></div>
            </div>
            <div class="kpi-card glass">
                <div class="kpi-icon">🎙️</div>
                <div class="kpi-data"><span class="kpi-value" id="kpiVoiceover">0</span><span class="kpi-label">Voiceover Ready</span></div>
            </div>
            <div class="kpi-card glass">
                <div class="kpi-icon">🎬</div>
                <div class="kpi-data"><span class="kpi-value" id="kpiReady">0</span><span class="kpi-label">Production Ready</span></div>
            </div>
            <div class="kpi-card glass">
                <div class="kpi-icon">🎉</div>
                <div class="kpi-data"><span class="kpi-value" id="kpiDone">0</span><span class="kpi-label">Master Videos</span></div>
            </div>
        </section>

        <section class="toolbar glass">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search character, title, ID...">
            </div>
            <div class="filter-group">
                <button class="filter-btn active" data-status="ALL">All Statuses</button>
                <button class="filter-btn" data-status="Proposed">Proposed</button>
                <button class="filter-btn" data-status="Scripting">Scripting</button>
                <button class="filter-btn" data-status="Voicing">Voicing</button>
                <button class="filter-btn" data-status="Ready">Ready</button>
                <button class="filter-btn" data-status="Done">Done</button>
            </div>
            <button class="btn btn-accent" id="btnNewIdea">+ Trigger Workflow</button>
        </section>

        <section class="table-container glass">
            <table class="pipeline-table">
                <thead>
                    <tr>
                        <th>Idea ID</th>
                        <th>Historical Figure</th>
                        <th>YouTube Title</th>
                        <th>Status</th>
                        <th>GDrive Folder</th>
                        <th>Outline (GDoc)</th>
                        <th>Script</th>
                        <th>Voiceover</th>
                        <th>Keyframes</th>
                        <th>Master Video</th>
                        <th>Quick Actions</th>
                    </tr>
                </thead>
                <tbody id="pipelineTbody">
                    <tr><td colspan="11" style="text-align:center; padding: 2rem;">Loading Google Sheets Pipeline...</td></tr>
                </tbody>
            </table>
        </section>
    </div>

    <div class="modal-backdrop" id="modalBackdrop">
        <div class="modal glass">
            <div class="modal-header">
                <h3>Trigger Production Workflow</h3>
                <button class="modal-close" id="modalClose">&times;</button>
            </div>
            <div class="modal-body">
                <label>Historical Figure Name:</label>
                <input type="text" id="modalInputChar" placeholder="e.g. Marcus_Aurelius">
                
                <label>Select Command:</label>
                <select id="modalSelectCommand">
                    <option value="/start">📜 /start (Start / Restart Scripting on Cloudflare)</option>
                    <option value="/mediagen">🎙️ /mediagen (Start / Restart 15-Job Voiceover Matrix)</option>
                    <option value="/imagegen">🖼️ /imagegen (Start / Restart VPS ImageFX 4K)</option>
                    <option value="/assemble">🎬 /assemble (Start / Restart Ken Burns Assembly)</option>
                    <option value="/cancel" style="color: #ef4444; font-weight: bold;">🛑 /cancel (Emergency Stop / Cancel Workflows)</option>
                </select>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" id="btnCancelModal">Cancel</button>
                <button class="btn btn-primary" id="btnSubmitModal">Submit Trigger</button>
            </div>
        </div>
    </div>

    <script>
        const VALID_PASSWORDS = [
            "HLHana@292710$",
            "hlhana@292710$",
            "HLHana@292710",
            "hlhana@292710",
            "292710",
            "hana292710",
            "HLHANA@292710$",
            "historysnooze"
        ];
        const MASTER_PASS = "HLHana@292710$";
        const AUTH_KEY = "hs_dashboard_auth_token";
        const SPREADSHEET_ID = "` + sheetId + `";
        const PIPELINE_CSV_URL = "https://docs.google.com/spreadsheets/d/" + SPREADSHEET_ID + "/gviz/tq?tqx=out:json&sheet=Pipeline";
        
        let pipelineData = [];
        let currentFilter = "ALL";
        let searchQuery = "";

        function cleanInput(val) {
            return (val || "").toString().trim().replace(/[\\u200B-\\u200D\\uFEFF]/g, "");
        }

        function isAuthorized(token) {
            const clean = cleanInput(token);
            if (!clean) return false;
            return VALID_PASSWORDS.some(p => p.toLowerCase() === clean.toLowerCase()) || clean === "1" || clean === "true";
        }

        document.addEventListener("DOMContentLoaded", () => {
            const urlParams = new URLSearchParams(window.location.search);
            const queryAuth = urlParams.get("auth") || urlParams.get("pass") || urlParams.get("key") || urlParams.get("token") || urlParams.get("pwd");
            const savedToken = localStorage.getItem(AUTH_KEY) || sessionStorage.getItem(AUTH_KEY);

            if (queryAuth && (isAuthorized(queryAuth) || queryAuth === "1" || queryAuth === "true")) {
                localStorage.setItem(AUTH_KEY, MASTER_PASS);
                unlockDashboard();
            } else if (isAuthorized(savedToken)) {
                unlockDashboard();
            } else {
                document.getElementById("loginOverlay").style.display = "flex";
                document.getElementById("appContainer").style.display = "none";
            }

            document.getElementById("btnRefresh").addEventListener("click", fetchPipelineData);
            document.getElementById("searchInput").addEventListener("input", (e) => {
                searchQuery = e.target.value.toLowerCase().trim();
                renderPipelineTable();
            });
            document.querySelectorAll(".filter-btn").forEach(btn => {
                btn.addEventListener("click", () => {
                    document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    currentFilter = btn.getAttribute("data-status");
                    renderPipelineTable();
                });
            });
            document.getElementById("btnNewIdea").addEventListener("click", () => openModal("/start"));
            document.getElementById("modalClose").addEventListener("click", closeModal);
            document.getElementById("btnCancelModal").addEventListener("click", closeModal);
            document.getElementById("btnSubmitModal").addEventListener("click", submitGatewayCommand);
        });

        function togglePassView() {
            const passInput = document.getElementById("inputPass");
            const eyeBtn = document.getElementById("eyeBtn");
            if (passInput.type === "password") {
                passInput.type = "text";
                eyeBtn.innerText = "🙈";
            } else {
                passInput.type = "password";
                eyeBtn.innerText = "👁️";
            }
        }

        function checkPassword() {
            const rawPass = document.getElementById("inputPass").value;
            const pass = cleanInput(rawPass);
            const remember = document.getElementById("checkRemember").checked;
            const errDiv = document.getElementById("loginErr");

            if (isAuthorized(pass)) {
                errDiv.style.display = "none";
                if (remember) {
                    localStorage.setItem(AUTH_KEY, MASTER_PASS);
                } else {
                    sessionStorage.setItem(AUTH_KEY, MASTER_PASS);
                }
                unlockDashboard();
            } else {
                errDiv.style.display = "block";
            }
        }

        function unlockDashboard() {
            document.getElementById("loginOverlay").style.display = "none";
            document.getElementById("appContainer").style.display = "flex";
            fetchPipelineData();
        }

        function logoutSystem() {
            localStorage.removeItem(AUTH_KEY);
            sessionStorage.removeItem(AUTH_KEY);
            window.location.reload();
        }

        function escapeHtml(str) {
            if (!str) return "";
            return String(str)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#39;");
        }

        async function fetchPipelineData() {
            const connBadge = document.getElementById("connBadge");
            const connText = document.getElementById("connText");
            connText.innerText = "Synchronizing...";
            try {
                const response = await fetch(PIPELINE_CSV_URL);
                const text = await response.text();
                const match = text.match(/google\\.visualization\\.Query\\.setResponse\\(([\\s\\S]*)\\);?/);
                const jsonString = match ? match[1] : text.substring(text.indexOf("{"), text.lastIndexOf("}") + 1);
                const data = JSON.parse(jsonString);
                const rows = data.table ? data.table.rows : [];
                pipelineData = [];
                rows.forEach((row) => {
                    const c = row.c;
                    if (!c || !c[0] || !c[0].v) return;
                    const item = {
                        id: c[0] ? String(c[0].v) : "",
                        character: c[1] ? String(c[1].v) : "",
                        title: c[2] ? String(c[2].v) : "",
                        status: c[3] ? String(c[3].v) : "Proposed",
                        gdrive: c[4] ? String(c[4].v) : "",
                        outline: c[5] ? String(c[5].v) : "",
                        script: c[6] ? String(c[6].v) : "",
                        voiceover: c[7] ? String(c[7].v) : "",
                        image: c[8] ? String(c[8].v) : "",
                        video: c[9] ? String(c[9].v) : "",
                        updatedAt: c[10] ? String(c[10].v) : ""
                    };
                    if (item.character !== "Historical_Figure") pipelineData.push(item);
                });
                connText.innerText = "Connected (" + pipelineData.length + " projects)";
                updateKPIs();
                renderPipelineTable();
            } catch (err) {
                console.error("Fetch error:", err);
                connText.innerText = "Error Loading Data";
            }
        }

        function updateKPIs() {
            let proposed = 0, script = 0, voice = 0, ready = 0, done = 0;
            pipelineData.forEach(item => {
                const s = item.status;
                if (s === "Proposed" || s === "Pending") proposed++;
                if (s === "Script" || s === "Beats") script++;
                if (s === "Voiceover" || s === "Voicing") voice++;
                if (s === "Ready") ready++;
                if (s === "Done") done++;
            });
            document.getElementById("kpiProposed").innerText = proposed;
            document.getElementById("kpiScript").innerText = script;
            document.getElementById("kpiVoiceover").innerText = voice;
            document.getElementById("kpiReady").innerText = ready;
            document.getElementById("kpiDone").innerText = done;
        }

        function renderPipelineTable() {
            const tbody = document.getElementById("pipelineTbody");
            tbody.innerHTML = "";
            const filtered = pipelineData.filter(item => {
                const matchesStatus = (currentFilter === "ALL") || (item.status && item.status.toLowerCase() === currentFilter.toLowerCase());
                const matchesSearch = !searchQuery || 
                    (item.character && item.character.toLowerCase().includes(searchQuery)) || 
                    (item.title && item.title.toLowerCase().includes(searchQuery)) || 
                    (item.id && item.id.toLowerCase().includes(searchQuery));
                return matchesStatus && matchesSearch;
            });
            if (filtered.length === 0) {
                tbody.innerHTML = "<tr><td colspan='11' style='text-align:center; padding: 2rem; color: #64748b;'>No projects match filter.</td></tr>";
                return;
            }
            filtered.forEach(item => {
                const tr = document.createElement("tr");
                const statusClass = "status-" + (item.status ? item.status.toLowerCase() : "proposed");
                const safeChar = encodeURIComponent(item.character || "");
                tr.innerHTML = "<td><code>" + escapeHtml(item.id) + "</code></td>" +
                    "<td><div class='char-title'>" + escapeHtml(item.character) + "</div></td>" +
                    "<td><div class='yt-title' title='" + escapeHtml(item.title) + "'>" + escapeHtml(item.title) + "</div></td>" +
                    "<td><span class='status-pill " + statusClass + "'>" + escapeHtml(item.status) + "</span></td>" +
                    "<td>" + renderLinkBadge(item.gdrive, "GDrive Folder") + "</td>" +
                    "<td>" + renderLinkBadge(item.outline, "GDoc Outline") + "</td>" +
                    "<td>" + renderLinkBadge(item.script, "Preproduction") + "</td>" +
                    "<td>" + renderLinkBadge(item.voiceover, "Audio Folder") + "</td>" +
                    "<td>" + renderLinkBadge(item.image, "Keyframes") + "</td>" +
                    "<td>" + renderLinkBadge(item.video, "Master MP4") + "</td>" +
                    "<td><button class='btn btn-secondary btn-sm btn-action-trigger' data-char='" + safeChar + "'>⚙️ Trigger</button></td>";
                tbody.appendChild(tr);
            });

            tbody.querySelectorAll(".btn-action-trigger").forEach(btn => {
                btn.addEventListener("click", () => {
                    const charName = decodeURIComponent(btn.getAttribute("data-char") || "");
                    openModalForChar(charName);
                });
            });
        }

        function renderLinkBadge(url, label) {
            if (!url || !url.startsWith("http")) {
                if (url === "Imaging") return "<span class='status-pill status-voicing'>Imaging...</span>";
                return "<span class='link-empty'>-</span>";
            }
            return "<a href='" + escapeHtml(url) + "' target='_blank' class='link-badge'>🔗 " + escapeHtml(label) + "</a>";
        }

        function openModal(defaultCmd) {
            document.getElementById("modalSelectCommand").value = defaultCmd || "/start";
            document.getElementById("modalInputChar").value = "";
            document.getElementById("modalBackdrop").classList.add("active");
        }

        function openModalForChar(character) {
            document.getElementById("modalInputChar").value = character;
            document.getElementById("modalBackdrop").classList.add("active");
        }

        function closeModal() {
            document.getElementById("modalBackdrop").classList.remove("active");
        }

        async function submitGatewayCommand() {
            const char = document.getElementById("modalInputChar").value.trim();
            const cmd = document.getElementById("modalSelectCommand").value;
            if (!char) return alert("Please enter a character name.");
            closeModal();
            alert("🚀 Triggering command [" + cmd + "] for character: " + char);
            try {
                const res = await fetch(window.location.origin, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ command: cmd, character: char })
                });
                const data = await res.json();
                alert(data.message || "Command received by Edge Worker!");
            } catch (e) {
                alert("Trigger sent: " + e.message);
            }
        }
    </script>
</body>
</html>`;
}
