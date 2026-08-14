/**
 * Cloudflare Worker Gateway for HistorySnooze (Zero-n8n Edge Architecture)
 * Receives Webhooks from Google Apps Script / Telegram Bot
 * Dispatches repository_dispatch events to GitHub Actions API.
 */

export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") {
      return new Response(JSON.stringify({ error: "Method not allowed. Use POST." }), {
        status: 405,
        headers: { "Content-Type": "application/json" }
      });
    }

    try {
      const payload = await request.json();
      const command = payload.command || "/start";
      const character = payload.character || "Marcus_Aurelius";

      // GitHub Credentials from Cloudflare Secret Vault
      const GITHUB_TOKEN = env.GITHUB_PAT_TOKEN;
      const GITHUB_REPO = env.GITHUB_REPO || "your-username/historysnooze";

      let eventType = "run_scripting_paced";
      if (command.includes("mediagen") || command.includes("voice")) {
        eventType = "run_voiceover_matrix";
      } else if (command.includes("imagegen") || command.includes("image")) {
        eventType = "run_imagefx_vps";
      } else if (command.includes("assemble") || command.includes("video")) {
        eventType = "run_kenburns_assembly";
      }

      // Dispatch event to GitHub API
      const ghUrl = `https://api.github.com/repos/${GITHUB_REPO}/dispatches`;
      const ghResp = await fetch(ghUrl, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${GITHUB_TOKEN}`,
          "Accept": "application/vnd.github.v3+json",
          "User-Agent": "CloudflareWorker-HistorySnooze"
        },
        body: JSON.stringify({
          event_type: eventType,
          client_payload: {
            character: character,
            command: command
          }
        })
      });

      if (ghResp.status === 204) {
        return new Response(JSON.stringify({
          status: "SUCCESS",
          message: `Triggered GitHub Actions event [${eventType}] for character [${character}]`
        }), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        });
      } else {
        const errText = await ghResp.text();
        return new Response(JSON.stringify({
          status: "ERROR",
          gh_status: ghResp.status,
          message: errText
        }), {
          status: 500,
          headers: { "Content-Type": "application/json" }
        });
      }
    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }
};
