/**
 * Google Apps Script for HistorySnooze Master Pipeline
 * 100% Cloudflare Edge Gateway Integrated (No local Gemini keys needed)
 * Gateway URL: https://historysnooze-gateway.hothihuong113.workers.dev
 */

const DEFAULT_GATEWAY_URL = "https://historysnooze-gateway.hothihuong113.workers.dev";

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu("🚀 HistorySnooze Menu")
    .addItem("💡 Run 2-Step Ideation Wizard (/idea)", "triggerIdeationWizard")
    .addItem("🌐 Open WebApp Dashboard (Cloudflare)", "openDashboardUrl")
    .addItem("⚙️ Set Gateway URL", "setGatewayUrl")
    .addSeparator()
    .addItem("📜 Start Pre-Production (/start)", "triggerPreproduction")
    .addItem("🎙️ Generate Voiceovers (/mediagen)", "triggerVoiceover")
    .addItem("🖼️ Trigger VPS ImageFX (/imagegen)", "triggerImagegen")
    .addItem("🎬 Assemble Master Video (/assemble)", "triggerAssembly")
    .addToUi();
}

function getGatewayUrl() {
  return PropertiesService.getScriptProperties().getProperty("CLOUDFLARE_WORKER_URL") || DEFAULT_GATEWAY_URL;
}

function setGatewayUrl() {
  const ui = SpreadsheetApp.getUi();
  const currentUrl = getGatewayUrl();
  const response = ui.prompt(
    "⚙️ Set Cloudflare Gateway URL",
    `Current URL: ${currentUrl}\nEnter your deployed Cloudflare Worker URL:`,
    ui.ButtonSet.OK_CANCEL
  );
  if (response.getSelectedButton() === ui.Button.OK) {
    const url = response.getResponseText().trim();
    if (url) {
      PropertiesService.getScriptProperties().setProperty("CLOUDFLARE_WORKER_URL", url);
      ui.alert("✅ Cloudflare Worker Gateway URL updated successfully!");
    }
  }
}

function openDashboardUrl() {
  const gatewayUrl = getGatewayUrl();
  const html = HtmlService.createHtmlOutput(
    `<script>window.open('${gatewayUrl}', '_blank');google.script.host.close();</script>`
  ).setWidth(200).setHeight(50);
  SpreadsheetApp.getUi().showModalDialog(html, "Opening HistorySnooze WebApp...");
}

function triggerIdeationWizard() {
  const html = HtmlService.createHtmlOutputFromFile('IdeationWizard')
      .setWidth(560)
      .setHeight(620)
      .setTitle('💡 HistorySnooze - 2-Step AI Ideation Wizard');
  SpreadsheetApp.getUi().showModalDialog(html, ' ');
}

function getBlacklistEntries() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const blacklistSheet = ss.getSheetByName("Blacklist");
  if (!blacklistSheet) return [];

  const lastRow = blacklistSheet.getLastRow();
  if (lastRow < 2) return [];

  const values = blacklistSheet.getRange("B2:B" + lastRow).getValues();
  const list = [];
  for (let i = 0; i < values.length; i++) {
    if (values[i][0] && values[i][0].toString().trim()) {
      list.push(values[i][0].toString().trim());
    }
  }
  return list;
}

function getFiguresFromWorker(keyword) {
  const blacklist = getBlacklistEntries();
  const kw = keyword.trim();
  const workerUrl = getGatewayUrl();

  const options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({ keyword: kw, blacklist: blacklist }),
    muteHttpExceptions: true
  };

  try {
    const res = UrlFetchApp.fetch(`${workerUrl}/api/ideation/suggest-figures`, options);
    const data = JSON.parse(res.getContentText());
    if (data.status === "SUCCESS" && data.figures && data.figures.length > 0) {
      const blLower = blacklist.map(b => b.toLowerCase());
      return data.figures.filter(f => !blLower.includes(f.character.toLowerCase()));
    }
    throw new Error(data.message || "Failed to fetch figures from Gateway.");
  } catch (e) {
    Logger.log("Worker error in getFiguresFromWorker: " + e);
    // Dynamic Fallback
    return generateDynamicFallbackFigures(kw, blacklist);
  }
}

function generateDynamicFallbackFigures(keyword, blacklist) {
  const blLower = blacklist.map(b => b.toLowerCase());
  const kw = keyword.trim();

  const fallbackFigures = [
    { id: 1, character: `Key Figure 1 of ${kw}`, summary: `Prominent historical leader and visionary during the era of ${kw}.` },
    { id: 2, character: `Key Figure 2 of ${kw}`, summary: `Renowned cultural and intellectual figure who shaped ${kw}.` },
    { id: 3, character: `Key Figure 3 of ${kw}`, summary: `Influential reformer and strategist of ${kw}.` },
    { id: 4, character: `Key Figure 4 of ${kw}`, summary: `Famous military commander associated with ${kw}.` },
    { id: 5, character: `Key Figure 5 of ${kw}`, summary: `Celebrated historical figure from ${kw}.` }
  ];

  return fallbackFigures.filter(f => !blLower.includes(f.character.toLowerCase()));
}

function getTitlesFromWorker(character) {
  const workerUrl = getGatewayUrl();

  const options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({ character: character }),
    muteHttpExceptions: true
  };

  try {
    const res = UrlFetchApp.fetch(`${workerUrl}/api/ideation/suggest-titles`, options);
    const data = JSON.parse(res.getContentText());
    if (data.status === "SUCCESS" && data.titles && data.titles.length > 0) {
      return data.titles;
    }
    throw new Error(data.message || "Failed to fetch titles from Gateway.");
  } catch (e) {
    Logger.log("Worker error in getTitlesFromWorker: " + e);
    return [
      `${character}: The Night Writing Legend & Hidden Secrets`,
      `${character}: Sleepy History Whispers for Deep Relaxation`,
      `${character}: Sleepless Nights & The Forgotten Chronicles`,
      `${character}: Secret Life & Eternal Historical Legacy`,
      `${character}: The Ultimate ASMR Sleep History Documentary`
    ];
  }
}

function insertIdeaToPipeline(character, title) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const pipelineSheet = ss.getSheetByName("Pipeline");
  const blacklistSheet = ss.getSheetByName("Blacklist");
  if (!pipelineSheet) return false;

  const ideaId = "id_" + Math.random().toString(36).substring(2, 8);
  const timestamp = Utilities.formatDate(new Date(), "GMT+7", "yyyy-MM-dd HH:mm:ss");

  // 1. Insert into Pipeline Sheet (A:K)
  const newPipelineRow = [
    ideaId, character, title, "Proposed",
    "", "", "", "", "", "", timestamp
  ];
  pipelineSheet.appendRow(newPipelineRow);

  // 2. Immediately Auto-Sync to Blacklist Sheet if not already present
  if (blacklistSheet) {
    const existingBl = getBlacklistEntries().map(b => b.toLowerCase());
    if (!existingBl.includes(character.toLowerCase())) {
      const nextNo = blacklistSheet.getLastRow();
      const newBlacklistRow = [
        nextNo, character, "Pipeline", "Proposed", timestamp
      ];
      blacklistSheet.appendRow(newBlacklistRow);
    }
  }

  return true;
}

function getSelectedCharacter() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const activeCell = sheet.getActiveCell();
  const row = activeCell.getRow();
  
  if (row >= 2) {
    const charName = sheet.getRange(row, 2).getValue();
    if (charName && charName.toString().trim() && !charName.toString().includes("Historical_Figure")) {
      return charName.toString().trim();
    }
  }
  
  const ui = SpreadsheetApp.getUi();
  const response = ui.prompt("🚀 HistorySnooze", "Enter historical character name (or select a row in Pipeline):", ui.ButtonSet.OK_CANCEL);
  if (response.getSelectedButton() === ui.Button.OK) {
    const inputChar = response.getResponseText().trim();
    if (inputChar) return inputChar;
  }
  return null;
}

function callGateway(command, character) {
  const workerUrl = getGatewayUrl();
  const options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({ command: command, character: character }),
    muteHttpExceptions: true
  };
  try {
    const response = UrlFetchApp.fetch(workerUrl, options);
    const result = JSON.parse(response.getContentText());
    if (result.status === "SUCCESS") {
      SpreadsheetApp.getUi().alert(`✅ Triggered [${command}] for character: ${character}\n\n${result.message || ''}`);
    } else {
      SpreadsheetApp.getUi().alert(`❌ Gateway Error: ${result.message}`);
    }
  } catch (err) {
    SpreadsheetApp.getUi().alert(`❌ Gateway Connection Error: ${err.message}`);
  }
}

function triggerPreproduction() {
  const char = getSelectedCharacter();
  if (char) callGateway("/start", char);
}

function triggerVoiceover() {
  const char = getSelectedCharacter();
  if (char) callGateway("/mediagen", char);
}

function triggerAssembly() {
  const char = getSelectedCharacter();
  if (char) callGateway("/assemble", char);
}

function triggerImagegen() {
  const char = getSelectedCharacter();
  if (char) callGateway("/imagegen", char);
}
