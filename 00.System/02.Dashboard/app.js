// HistorySnooze WebApp Dashboard Logic (100% English)
const CLOUDFLARE_WORKER_URL = "https://historysnooze-gateway.hothihuong113.workers.dev";
const SPREADSHEET_ID = "1x2tcR4WyHXj_cvHjpPFWNsrtelkimUXJXNTw9hPbVeo";

const PIPELINE_CSV_URL = `https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}/gviz/tq?tqx=out:json&sheet=Pipeline`;

let pipelineData = [];
let currentFilter = "ALL";
let searchQuery = "";

document.addEventListener("DOMContentLoaded", () => {
    fetchPipelineData();

    // Event Listeners
    document.getElementById("btnRefresh").addEventListener("click", fetchPipelineData);
    document.getElementById("searchInput").addEventListener("input", (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        renderPipelineTable();
    });

    // Filter Buttons
    document.querySelectorAll(".filter-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentFilter = btn.getAttribute("data-status");
            renderPipelineTable();
        });
    });

    // Modal Events
    document.getElementById("btnNewIdea").addEventListener("click", () => openModal("/idea"));
    document.getElementById("modalClose").addEventListener("click", closeModal);
    document.getElementById("btnCancelModal").addEventListener("click", closeModal);
    document.getElementById("btnSubmitModal").addEventListener("click", submitGatewayCommand);
});

async function fetchPipelineData() {
    const connBadge = document.getElementById("connBadge");
    const connText = document.getElementById("connText");
    const tbody = document.getElementById("pipelineTbody");

    connText.innerText = "Synchronizing data...";
    
    try {
        const response = await fetch(PIPELINE_CSV_URL);
        const text = await response.text();
        
        const jsonString = text.substring(47, text.length - 2);
        const data = JSON.parse(jsonString);

        const rows = data.table.rows;
        pipelineData = [];

        rows.forEach((row, idx) => {
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

            if (item.character !== "Historical_Figure") {
                pipelineData.push(item);
            }
        });

        connText.innerText = `Connected (${pipelineData.length} projects)`;
        connBadge.className = "connection-badge online";
        
        updateKPIs();
        renderPipelineTable();

    } catch (err) {
        console.error("Fetch Error:", err);
        connText.innerText = "GSheet Connection Error";
        connBadge.className = "connection-badge offline";
        
        renderFallbackMockData();
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
        const matchesStatus = (currentFilter === "ALL") || (item.status.toLowerCase() === currentFilter.toLowerCase());
        const matchesSearch = !searchQuery || 
            item.character.toLowerCase().includes(searchQuery) ||
            item.title.toLowerCase().includes(searchQuery) ||
            item.id.toLowerCase().includes(searchQuery);
        return matchesStatus && matchesSearch;
    });

    if (filtered.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="11" class="loading-state">
                    <p>No projects match the selected filter.</p>
                </td>
            </tr>
        `;
        return;
    }

    filtered.forEach(item => {
        const tr = document.createElement("tr");

        const statusClass = `status-${item.status.toLowerCase()}`;
        
        tr.innerHTML = `
            <td><code>${item.id}</code></td>
            <td><div class="char-title">${item.character}</div></td>
            <td><div class="yt-title" title="${item.title}">${item.title}</div></td>
            <td><span class="status-pill ${statusClass}">${item.status}</span></td>
            <td>${renderLinkBadge(item.gdrive, "GDrive Root")}</td>
            <td>${renderLinkBadge(item.outline, "GDoc Outline")}</td>
            <td>${renderLinkBadge(item.script, "Preproduction")}</td>
            <td>${renderLinkBadge(item.voiceover, "Audio Folder")}</td>
            <td>${renderLinkBadge(item.image, "Keyframes Folder")}</td>
            <td>${renderLinkBadge(item.video, "Master MP4")}</td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="openModalForChar('${item.character}')">
                    ⚙️ Quick Action
                </button>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

function renderLinkBadge(url, label) {
    if (!url || !url.startsWith("http")) {
        if (url === "Imaging") return `<span class="status-pill status-imaging">Imaging...</span>`;
        return `<span class="link-empty">-</span>`;
    }
    return `
        <a href="${url}" target="_blank" class="link-badge">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            ${label}
        </a>
    `;
}

function openModal(defaultCmd = "/start") {
    document.getElementById("modalSelectCommand").value = defaultCmd;
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

    if (!char && cmd !== "/idea") {
        alert("Please enter a historical character name.");
        return;
    }

    closeModal();
    alert(`🚀 Triggered command [${cmd}] for character: ${char || 'Keyword Suggestion'}`);
    
    try {
        const res = await fetch(CLOUDFLARE_WORKER_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: cmd, character: char })
        });
        const data = await res.json();
        console.log("Gateway response:", data);
    } catch (e) {
        console.warn("Gateway notice:", e);
    }
}

function renderFallbackMockData() {
    pipelineData = [
        {
            id: "id_m1a2u3",
            character: "Marcus Aurelius",
            title: "Marcus Aurelius: The Stoic Emperor Writing Meditations By Night",
            status: "Done",
            gdrive: "https://drive.google.com/drive/u/0/folders/1UGkrUFQ62ghj1Lquy1HVsKIYR9nO60zf",
            outline: "https://docs.google.com/document/d/1sample_outline",
            script: "https://drive.google.com/drive/u/0/folders/1sample_script",
            voiceover: "https://drive.google.com/drive/u/0/folders/1sample_audio",
            image: "https://drive.google.com/drive/u/0/folders/1sample_keyframes",
            video: "https://drive.google.com/file/d/1sample_video/view",
            updatedAt: "2026-08-14 15:45:00"
        }
    ];
    updateKPIs();
    renderPipelineTable();
}
