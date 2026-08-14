# HISTORYSNOOZE (100% ONLINE CLOUD SYSTEM) - MASTER HANDOFF MANUAL

> [!IMPORTANT]
> Đây là tài liệu bàn giao **DUY NHẤT & CHÍNH THỨC** của hệ thống **HISTORYSNOOZE MỚI 100% ONLINE** (đặt tại `/media/vpsg16gb/HaRiDisk/Youtube/historysnooze`).
> Toàn bộ quy trình điều phối và giao diện vận hành 100% trên Cloud/Edge. Lưu trữ tập trung 100% trên Google Drive (Folder ID: `1UGkrUFQ62ghj1Lquy1HVsKIYR9nO60zf`).

---

## 🌐 1. Các Đường Dẫn Vận Hành Hệ Thống (Master Endpoints)

| Chức năng | Liên kết / Thông tin | Ghi chú |
| :--- | :--- | :--- |
| **Global WebApp Control Center** | 👉 [historysnooze-gateway.hothihuong113.workers.dev](https://historysnooze-gateway.hothihuong113.workers.dev) | Giao diện điều hành Dark Glassmorphic 100% Online |
| **Mật khẩu truy cập WebApp** | `HLHana@292710$` | Hỗ trợ nút **👁️ xem mật khẩu** & **Remember me** ghi nhớ đăng nhập |
| **Google Sheets Pipeline** | [Master Pipeline Spreadsheet](https://docs.google.com/spreadsheets/d/1x2tcR4WyHXj_cvHjpPFWNsrtelkimUXJXNTw9hPbVeo) | Bảng điều phối dự án & 2-Step Ideation Wizard |
| **Google Drive Parent Folder** | `1UGkrUFQ62ghj1Lquy1HVsKIYR9nO60zf` | Lưu trữ 100% kho dữ liệu Preproduction & Video Master |
| **GitHub Actions Dispatcher** | [naadld/hizzsnuve/actions](https://github.com/naadld/hizzsnuve/actions) | Máy chủ đám mây chạy 15 parallel TTS jobs & render MP4 |

---

## 🤖 2. Bể 10 AI API Keys & Cơ Chế Xoay Vòng Chịu Lỗi (10-Key Multi-Tier AI Edge)

Cloudflare Worker Edge tự động điều phối xoay vòng bể 10 AI API Keys theo thứ tự ưu tiên 3 tầng:

```text
               ┌────────────────────────────────────────────────────────┐
               │ 💡 Gửi Yêu Cầu AI (Ideation / Filtering / Scripting)   │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 1: 6-Key Gemini API Rotation Pool (GEMINI_KEY_1 ... GEMINI_KEY_6)               │
│ └─ Cân bằng tải xoay vòng ngẫu nhiên giữa 6 keys Gemini API.                         │
│ └─ Xử lý các tác vụ suy luận sâu (15 tập kịch bản & phân đoạn beats).                │
└──────────────────────────────────────────┬───────────────────────────────────────────┘
                                           │ (Nếu hết Quota / Gặp lỗi Rate Limit)
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 2: 4-Key Agnes AI API Pool (EXTRA_AI_KEY_1 ... EXTRA_AI_KEY_4)                  │
│ └─ Kết nối máy chủ https://apihub.agnes-ai.com/v1 với model agnes-2.5-flash.         │
│ └─ Xử lý siêu tốc cho lọc từ khóa, gợi ý nhân vật & dàn ý.                           │
└──────────────────────────────────────────┬───────────────────────────────────────────┘
                                           │ (Kênh dự phòng 0$ cuối cùng)
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 3: Cloudflare Workers AI Free Tier (@cf/deepseek-ai/deepseek-r1-distill-qwen-32b)│
│ └─ Chạy trực tiếp trên Edge Cloudflare với 10,000 Free Daily Neurons mỗi ngày.        │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎛️ 3. Quy Trình 5 Bước Điều Hành Sản Xuất Video

```text
  [Google Sheets / WebApp Dashboard] 
            │ (Lệnh /idea, /start, /mediagen, /imagegen, /assemble)
            ▼
 ┌────────────────────────────────────────────────────────┐
 │ Cloudflare Worker Gateway (historysnooze-gateway)     │
 └──────────┬──────────────────────┬──────────────────────┘
            │                      │
   (Dispatch Workflows)      (Playwright CDP)
            ▼                      ▼
 ┌──────────────────────┐ ┌──────────────────────────────┐
 │ GitHub Actions       │ │ VPS Linux (Self-Hosted)      │
 │ ├─ 15 Parallel TTS   │ │ └─ Google ImageFX Automation │
 │ └─ FFmpeg Ken Burns  │ └──────────────┬───────────────┘
 └──────────┬───────────┘                │
            │ (Upload Assets)            │ (Upload Keyframes)
            ▼                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ Google Drive Hub (1UGkrUFQ62ghj1Lquy1HVsKIYR9nO60zf)  │
 │ ├─ 01.Preproduction (Scripts & Beats JSON)            │
 │ ├─ 02.Media Generation (Audio WAV, Keyframes, Combined│
 │ └─ 03.Final Production (Master MP4 Video)              │
 └────────────────────────────────────────────────────────┘
```

### 💡 Bước 1: Khởi Tạo Ý Tưởng (`/idea`)
* **Nền tảng**: Cloudflare WebApp Dashboard hoặc Google Sheets 2-Step Wizard.
* **Làm gì**: Nhập từ khóa ➔ AI lọc Blacklist, gợi ý 5 nhân vật + 5 tiêu đề YouTube chuẩn công thức kênh ➔ Bấm lưu vào Pipeline & Blacklist.

### 📜 Bước 2: Sinh Kịch Bản Theo Cơ Chế Part-by-Part (`/start`)
* **Nền tảng**: Cloudflare Worker Edge (Chia nhỏ gọi tuần tự 15 Parts, không lo Timeout).
* **Làm gì**: 
  1. Sinh `outline.json` (3 Hồi, 15 Parts).
  2. Vòng lặp Part 1 -> Part 15: Viết 750-900 từ/tập, ép 100% chữ số thành chữ, sinh Beats JSON tương ứng.
  3. Thanh tiến trình hiển thị realtime trên UI (`Part 1/15` ... `Part 15/15`).
  4. Đẩy 15 file `Part_XX_Voiceover.txt` và `Part_XX_beats.json` lên `01.Preproduction/` trên Google Drive.

### 📦 Bước 2.1: Tự Động Biên Dịch 2 File Combined
Ngay sau khi hoàn thành 15 tập kịch bản & beats, hệ thống tự động gộp và xuất 2 file đẩy vào `02.Media Generation/combined/`:
1. **`combined_voiceover.txt`**: Toàn bộ kịch bản 15 tập nối tiếp nhau có tiêu đề phân đoạn (`--- PART 01: [Title] --- ...`).
2. **`combined_imageprompts.txt`**: Toàn bộ danh sách prompts sinh ảnh, **ở đầu mỗi dòng bắt buộc ghi rõ tiêu đề file ảnh cần lưu và nằm trọn vẹn trên 1 dòng duy nhất**:
   ```text
   beat_P01_B01.jpg: [Core scene description...] — late-15th-century illuminated manuscript style painting, tempera and shell-gold, flat medieval perspective, fine brown-ink outlines, full-bleed edge-to-edge painting extending to all four edges of the 16:9 canvas, zero margins, no outer paper, no parchment border, no decorative frame, no page border, wide cinematic 16:9 composition, ultra-high-resolution (4K)
   beat_P01_B02.jpg: [Core scene description...] — late-15th-century illuminated manuscript style painting...
   ```

### 🎙️ Bước 3: Sinh Giọng Đọc Song Song (`/mediagen`)
* **Nền tảng**: GitHub Actions (`voiceover_matrix.yml`) chạy **15 Parallel Jobs**.
* **Làm gì**: Chạy OmniVoice TTS với giọng mẫu `historysnoozevoice_voice_milo.mp3` ➔ Sinh 15 file WAV chất lượng cao đưa vào `02.Media Generation/audio/`.

### 🖼️ Bước 4: Sinh Ảnh Keyframe Tràn Viền (`/imagegen`)
* **Nền tảng**: VPS Linux Playwright CDP (port 9222) kích hoạt qua `imagefx_vps.yml`.
* **Làm gì**: Điều khiển Google ImageFX sinh 45-60 bức ảnh illuminated manuscript tràn viền 16:9 4K đưa vào `02.Media Generation/keyframes/`.

### 🎬 Bước 5: Ghép Master Video MP4 (`/assemble`)
* **Nền tảng**: GitHub Actions (`assembly_kenburns.yml`) / FFmpeg.
* **Làm gì**: Nối 15 audio parts, áp dụng hiệu ứng chuyển động Ken Burns pan/zoom cho ảnh keyframes, render Master Video MP4 ➔ Upload lên `03.Final Production/` và đổi trạng thái Sheet sang `Done`.

---

## 🛡️ 4. Hệ Thống 7 Gatekeepers Kiểm Soát Chất Lượng

| Gatekeeper | Tên Chốt Chặn | Nền Tảng | Quy Tắc Kiểm Soát (Rule) |
| :---: | :--- | :--- | :--- |
| **GK1** | **Ideation & Outline** | Cloudflare Edge | • Lọc trùng tuyệt đối với tab `Blacklist`.<br>• Cấu trúc kịch bản đủ 3 Hồi & đúng 15 Phần. |
| **GK2** | **Script Quality & Words** | Cloudflare Edge | • Độ dài chuẩn **750 – 900 từ** / tập.<br>• **100% chữ số phải đổi thành chữ** (VD: *năm 1945* ➔ *năm một ngàn chín trăm bốn mươi lăm*).<br>• Không chứa nhãn `[NARRATOR]`, `[MUSIC]`.<br>• Đoạn mở đầu Part 1 bắt buộc có câu **"dim the light"**.<br>• **Quy tắc dấu câu & dấu chấm**: Chuẩn hóa `..` thành `.`, chuỗi `....` hoặc `.........` thành `...`, chuẩn hóa khoảng trắng sau dấu câu, loại bỏ hoàn toàn ký tự lạ/mojibake. |
| **GK3** | **Beats & Prompt Formula** | Cloudflare Edge | • Số lượng beat: Part 1 có 4 ảnh; Parts 2-14 có 4-5 ảnh; Part 15 có 3 ảnh.<br>• Prompt bắt buộc theo chuẩn: *Late-15th-century illuminated manuscript style painting, full-bleed edge-to-edge, zero margins, no frame, 16:9 4K*. |
| **GK4** | **Audio Validator & Auto-Retry** | GitHub Actions | • File WAV sinh ra bắt buộc có **dung lượng $\ge$ 10 KB**.<br>• **Kiểm định âm học chuyên sâu**:<br>  - *Chống file câm/mất tiếng*: Năng lượng RMS $\ge 0.003$, Peak $\ge 0.02$.<br>  - *Chống thiếu chunk/nuốt chữ*: Thời lượng phải tương ứng với số từ ($\ge 0.15s$ / từ).<br>  - *Chống lỗi tensor/méo tiếng*: Không chứa giá trị NaN/Inf.<br>• **Cơ chế Tự Động Thử Lại (Auto-Retry)**: Tự động chạy lại 3 lần ngay trong job nếu vi phạm GK4.<br>• **Cơ chế Re-run Độc Lập**: Tự động bỏ qua các Part đã Passed, chỉ tái sinh đúng Part bị lỗi.<br>• **Khoảng lặng ngắt nghỉ (Silence Pacing)**: 1.0s (chunks), 2.0s (paragraphs), 5.0s (parts).<br>• **Cấm 100% ký tự đặc biệt**: Lọc sạch `* # @ $ % ^ & _ ~ / \ | < > { } [ ] + =`. |
| **GK5** | **Image Physical Validator** | VPS Linux | • File ảnh tải về bắt buộc có **dung lượng $\ge$ 30 KB** (loại bỏ thumbnail lỗi). |
| **GK6** | **Pre-Render Asset Auditor** | GitHub Actions / VPS | • Kiểm toán trước khi render: Đảm bảo có đủ **15/15 audio parts** và **tối thiểu 15 ảnh keyframe** hợp lệ. |
| **GK7** | **Final Video Verification** | GitHub Actions / VPS | • Video Master MP4 hoàn thiện phải có **Duration > 0s**, âm thanh hình ảnh đồng bộ trước khi đẩy lên GDrive `03.Final Production/` và cập nhật `Done`. |

---

## ⏱️ 5. Quy Chuẩn Vàng Về Scripting, Chia Chunks & Khoảng Lặng Ngắt Nghỉ

### A. Cơ Chế Chia Nhỏ Chunk Theo Câu (Smart Sentence Chunking)
* **Tách theo ranh giới câu**: Tách văn bản kịch bản thành từng câu ngắn độc lập `(?<=[.!?])\s+` (độ dài lý tưởng 20–35 từ / câu).
* **Xử lý câu quá dài (> 180 ký tự)**: Tự động tách phụ theo các dấu ngắt vế `,`, `;`, `:`, `—` để OmniVoice luôn nhận các đoạn ngắn dễ đọc, triệt tiêu hoàn toàn hiện tượng nuốt chữ hoặc lặp từ (looping hallucination).

### B. Bảng Thời Gian Ngắt Nghỉ Tuyệt Đối (Silence Pacing)
1. **Giữa các Chunks trong cùng Paragraph**: Cách nhau đúng **`1.0 giây`** (`np.zeros(24000 * 1.0)`).
2. **Giữa các Paragraphs trong 1 Part**: Cách nhau đúng **`2.0 giây`** (`np.zeros(24000 * 2.0)`).
3. **Giữa các Parts khi ghép Video Master**: Cách nhau đúng **`5.0 giây`** (`silence_5s.wav`).

### C. Quy Tắc Xử Lý Dấu Chấm & Ký Tự Trong VoiceScript
* **Xử lý chuỗi dấu chấm**:
  * `..` (2 chấm) ➔ Chuyển thành **1 chấm `.`**.
  * `....` hoặc `.........` ($\ge 4$ chấm) ➔ Chuyển thành **dấu 3 chấm chuẩn `... `**.
  * Dấu `...` dính chữ ➔ Bắt buộc chèn 1 khoảng trắng sau `...` (`... `).
* **CẤM TUYỆT ĐỐI 100% Ký tự đặc biệt**:
  * Lọc sạch toàn bộ ký tự `* # @ $ % ^ & _ ~ / \ | < > { } [ ] + =` và nhãn `[NARRATOR]`, `[MUSIC]`, `(cười)`.
* **100% Chữ số phải đổi thành chữ viết**:
  * Bắt buộc chuyển: `1945` ➔ *năm một ngàn chín trăm bốn mươi lăm*, `18` ➔ *mười tám*.

### D. Kiến Trúc Phân Tầng Kiểm Soát (2-Layer Defense Architecture)

| Hạng mục kiểm soát | Nền tảng thực thi | File phụ trách | Cơ chế vận hành chi tiết |
| :--- | :---: | :--- | :--- |
| **1. Đổi 100% số thành chữ viết** | ☁️ **Cloudflare Edge** | [`worker_gateway.js`](file:///media/vpsg16gb/HaRiDisk/Youtube/historysnooze/00.System/00.Configuration/cloudflare_worker/worker_gateway.js) | Prompt AI ép viết thành chữ (*năm một ngàn chín trăm...*) |
| **2. Lọc sạch ký tự đặc biệt & nhãn** | ☁️ **Cloudflare Edge** | [`worker_gateway.js`](file:///media/vpsg16gb/HaRiDisk/Youtube/historysnooze/00.System/00.Configuration/cloudflare_worker/worker_gateway.js) | Regex loại bỏ `* # @ $ % ^ & _ ~ / \ | < > { } [ ] + =` và nhãn `[NARRATOR]`, `(cười)` |
| **3. Chuẩn hóa dấu `..` và `....`** | ☁️ **Cloudflare Edge** | [`worker_gateway.js`](file:///media/vpsg16gb/HaRiDisk/Youtube/historysnooze/00.System/00.Configuration/cloudflare_worker/worker_gateway.js) | `..` ➔ `.`, `....` hoặc `.........` ➔ `... ` |
| **4. Chia câu Chunks (< 180 ký tự)** | 🚀 **GitHub Actions** | [`omnivoice_tts_engine.py`](file:///media/vpsg16gb/HaRiDisk/Youtube/historysnooze/00.System/01.Scripts/omnivoice_tts_engine.py) | Hàm `split_paragraph_into_smart_chunks` tách nhỏ từng câu nạp vào OmniVoice |
| **5. Chèn 1.0s im lặng giữa các câu** | 🚀 **GitHub Actions** | [`omnivoice_tts_engine.py`](file:///media/vpsg16gb/HaRiDisk/Youtube/historysnooze/00.System/01.Scripts/omnivoice_tts_engine.py) | `np.zeros(24000 * 1.0)` giữa các chunks trong cùng paragraph |
| **6. Chèn 2.0s im lặng giữa các đoạn** | 🚀 **GitHub Actions** | [`omnivoice_tts_engine.py`](file:///media/vpsg16gb/HaRiDisk/Youtube/historysnooze/00.System/01.Scripts/omnivoice_tts_engine.py) | `np.zeros(24000 * 2.0)` giữa các paragraphs |
| **7. Chèn 5.0s im lặng giữa các Parts** | 🎬 **GitHub Actions** | [`kenburns_assembly.py`](file:///media/vpsg16gb/HaRiDisk/Youtube/historysnooze/00.System/01.Scripts/kenburns_assembly.py) | FFmpeg chèn `silence_5s.wav` giữa 15 parts khi ráp video master |

---

## 📁 6. Cấu Trúc Lưu Trữ Chuẩn Trên Google Drive (`1UGkrUFQ62ghj1Lquy1HVsKIYR9nO60zf`)

```text
📁 historysnooze posts/ (Parent Folder: 1UGkrUFQ62ghj1Lquy1HVsKIYR9nO60zf)
 └── 📁 <Character_Name>/ (e.g. Marcus_Aurelius)
      ├── 📁 01.Preproduction/
      │    ├── 📄 Google Doc Outline (GK1 Passed)
      │    ├── 📄 outline.json
      │    ├── 📄 Part_01_Voiceover.txt ... Part_15_Voiceover.txt
      │    └── 📄 Part_01_beats.json ... Part_15_beats.json
      ├── 📁 02.Media Generation/
      │    ├── 📁 audio/ (Part_01_Voiceover.wav ... Part_15_Voiceover.wav)
      │    ├── 📁 keyframes/ (beat_PXX_BYY.jpg ...)
      │    └── 📁 combined/ (combined_voiceover.txt, combined_imageprompts.txt)
      └── 📁 03.Final Production/
           └── 🎬 Master_<Character>_Documentary.mp4
```

---

## 📊 7. Google Sheets Master Pipeline Schema (`Pipeline!A:K`)

| Column | Header Name | Status & Lifecycle Description | Clickable GDrive Link |
| :---: | :--- | :--- | :--- |
| **A** | `Idea_ID` | Mã định danh duy nhất (VD: `id_a1b2c3`) | |
| **B** | `Historical_Figure` | Tên nhân vật lịch sử | |
| **C** | `YouTube_Title` | Tiêu đề YouTube chuẩn công thức kênh | |
| **D** | `Status` | `Proposed` ➔ `Pending` ➔ `Script` ➔ `Voiceover` ➔ `Ready` ➔ `Producing` ➔ `Done` | |
| **E** | `GDrive` | Link thư mục gốc của nhân vật trên GDrive | `https://drive.google.com/drive/u/0/folders/...` |
| **F** | `Outline` | Link Google Doc Outline trong `01.Preproduction/` | `https://docs.google.com/document/d/...` |
| **G** | `Script` | Link thư mục `01.Preproduction` (GK2 Passed) | `https://drive.google.com/drive/u/0/folders/...` |
| **H** | `Voiceover` | Link thư mục `02.Media Generation/audio/` (GK4 Passed) | `https://drive.google.com/drive/u/0/folders/...` |
| **I** | `Image` | Hiển thị `Imaging` khi đang chạy; link tới `keyframes/` | `https://drive.google.com/drive/u/0/folders/...` |
| **J** | `Video` | Link xem Master MP4 trên GDrive (GK7 Passed) | `https://drive.google.com/file/d/.../view` |
| **K** | `Updated_At` | Dấu thời gian cập nhật gần nhất (`YYYY-MM-DD HH:MM:SS`) | |

---

## 🎨 8. Công Thức Sinh Prompts Tràn Viền Chuẩn Kênh (Full-Bleed Edge-to-Edge)

`[Core scene description, key characters & actions, setting, mood, color accents] — late-15th-century illuminated manuscript style painting, tempera and shell-gold, flat medieval perspective, fine brown-ink outlines, full-bleed edge-to-edge painting extending to all four edges of the 16:9 canvas, zero margins, no outer paper, no parchment border, no decorative frame, no page border, wide cinematic 16:9 composition, ultra-high-resolution (4K)`
