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

### 🖼️ Bước 4: Sinh Ảnh Keyframe Tràn Viền Đa Chế Độ (`/imagegen` & Hybrid Mode)
* **Nền tảng**: VPS Linux Playwright CDP (port 9222) kết hợp Google Drive.
* **Hỗ trợ 3 Chế Độ Linh Hoạt (Triple-Mode Execution)**:
  * **Chế độ 1 (100% Tự động Auto-Pilot)**: VPS tự kết nối Chrome CDP cổng 9222, gõ prompt từ `combined_imageprompts.txt`, tải ảnh 4K gốc về, đổi tên `beat_PXX_BYY.jpg`, kiểm toán GK5 và upload lên GDrive `keyframes/`.
  * **Chế độ 2 (Anh tự tạo thủ công - Curated Art)**: Anh lấy prompt trong `combined_imageprompts.txt`, tự tạo ảnh trên Midjourney / Fooocus / ImageFX / Photoshop, đặt tên đúng chuẩn `beat_PXX_BYY.jpg` rồi kéo thả thẳng vào GDrive `02.Media Generation/keyframes/`. Hệ thống tự nhận diện và chuyển trạng thái sang `Ready`!
  * **Chế độ 3 (Lai ghép Hybrid)**: Nếu anh đã tự làm trước một số ảnh, VPS sẽ tự động bỏ qua các ảnh đã có (`[HYBRID SKIP]`) và chỉ sinh tự động những ảnh còn thiếu!

### 🎬 Bước 5: Ghép Master Video MP4 Bằng Phương Pháp Part-by-Part (`/assemble`)
* **Nền tảng**: GitHub Actions (`assembly_kenburns.yml`) / FFmpeg.
* **Quy trình thực thi (Method 1: Siêu nhẹ RAM, Chống OOM)**:
  1. **Dựng 15 Video Part độc lập**: Lấy audio `Part_XX_Voiceover.wav` + 3-5 ảnh tương ứng của Part đó ➔ Render `Part_XX_Video.mp4` (mỗi Part dài 5-7 phút, RAM chỉ tốn ~100MB).
  2. **Ghép siêu tốc thành Master Video**: Nối 15 video parts lại với nhau kèm **khoảng lặng 5.0 giây** (`silence_5s.mp4`) bằng lệnh `-c copy` chỉ mất 10 giây ➔ Xuất ra `Master_<Character>_Documentary.mp4`.
  3. **Kiểm tra GK7 & Hoàn tất**: Tự động tải Master MP4 lên Google Drive `03.Final Production/`, gắn link cột J và đổi trạng thái Sheet thành `Done`.

---

## 🛡️ 4. Hệ Thống 7 Gatekeepers Kiểm Soát Chất Lượng

| Gatekeeper | Tên Chốt Chặn | Nền Tảng | Quy Tắc Kiểm Soát (Rule) |
| :---: | :--- | :--- | :--- |
| **GK1** | **Ideation & Outline** | Cloudflare Edge | • Lọc trùng tuyệt đối với tab `Blacklist`.<br>• Cấu trúc kịch bản đủ 3 Hồi & đúng 15 Phần. |
| **GK2** | **Script Quality & Words** | Cloudflare Edge | • Độ dài chuẩn **750 – 900 từ** / tập.<br>• **100% chữ số phải đổi thành chữ** (VD: *năm 1945* ➔ *năm một ngàn chín trăm bốn mươi lăm*).<br>• Không chứa nhãn `[NARRATOR]`, `[MUSIC]`.<br>• Đoạn mở đầu Part 1 bắt buộc có câu **"dim the light"**.<br>• **Quy tắc dấu câu & dấu chấm**: Chuẩn hóa `..` thành `.`, chuỗi `....` hoặc `.........` thành `...`, chuẩn hóa khoảng trắng sau dấu câu, loại bỏ hoàn toàn ký tự lạ/mojibake. |
| **GK3** | **Beats & Prompt Formula** | Cloudflare Edge | • Số lượng beat: Part 1 có 4 ảnh; Parts 2-14 có 4-5 ảnh; Part 15 có 3 ảnh.<br>• Prompt bắt buộc theo chuẩn: *Late-15th-century illuminated manuscript style painting, full-bleed edge-to-edge, zero margins, no frame, 16:9 4K*. |
| **GK4** | **Audio Validator & Auto-Retry** | GitHub Actions | • File WAV sinh ra bắt buộc có **dung lượng $\ge$ 10 KB**.<br>• **Kiểm định âm học chuyên sâu**:<br>  - *Chống file câm/mất tiếng*: Năng lượng RMS $\ge 0.003$, Peak $\ge 0.02$.<br>  - *Chống thiếu chunk/nuốt chữ*: Thời lượng phải tương ứng với số từ ($\ge 0.15s$ / từ).<br>  - *Chống lỗi tensor/méo tiếng*: Không chứa giá trị NaN/Inf.<br>• **Cơ chế Tự Động Thử Lại (Auto-Retry)**: Tự động chạy lại 3 lần ngay trong job nếu vi phạm GK4.<br>• **Cơ chế Re-run Độc Lập**: Tự động bỏ qua các Part đã Passed, chỉ tái sinh đúng Part bị lỗi.<br>• **Khoảng lặng ngắt nghỉ (Silence Pacing)**: 1.0s (chunks), 2.0s (paragraphs), 5.0s (parts).<br>• **Cấm 100% ký tự đặc biệt**: Lọc sạch `* # @ $ % ^ & _ ~ / \ | < > { } [ ] + =`. |
| **GK5** | **Image Physical Validator** | VPS Linux | • Kích hoạt trực tiếp từ Cloudflare Worker sang VPS Listener (không qua trung gian GitHub).<br>• File ảnh tải về bắt buộc có **dung lượng $\ge$ 30 KB** (loại bỏ thumbnail lỗi/rỗng).<br>• Chuẩn tỷ lệ khung hình: **16:9 4K**. |
| **GK6** | **Pre-Assembly Asset Auditor** | GitHub Actions | • Kiểm toán trước khi render: Đảm bảo có đủ **15/15 audio parts** và **tối thiểu 15 ảnh keyframe** hợp lệ.<br>• Kiểm tra và render độc lập 15 video part nhỏ (`Part_01_Video.mp4` ... `Part_15_Video.mp4`) để tối ưu RAM (< 100MB). |
| **GK7** | **Final Video Verification** | GitHub Actions | • Video Master MP4 hoàn thiện (sau khi nối 15 Part + 5s silence) phải có **Duration > 0s** (đủ thời lượng chuẩn ~90 phút).<br>• Âm thanh, hình ảnh đồng bộ 100% trước khi đẩy lên GDrive `03.Final Production/` và cập nhật Sheet sang `Done`. |

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

## 📡 6. Vòng Phản Hồi Tín Hiệu 2 Chiều (Bi-Directional Telemetry & Gatekeeper Signals)

Toàn bộ các Gatekeepers trên GitHub Actions và VPS Linux đều được kết nối với **Cloudflare Worker Gateway** qua Webhook Callback: `POST /api/pipeline/callback`.

| Tín Hiệu (Event Signal) | Nguồn Phát | Ý Nghĩa Kỹ Thuật | Phản Ứng Của Cloudflare Worker |
| :--- | :---: | :--- | :--- |
| **`VOICEOVER_COMPLETED`** | GitHub Actions (Stage 3) | 15/15 Audio Parts đã hoàn thành xuất sắc GK4 và upload lên GDrive. | Lưu trạng thái Audio sẵn sàng; nếu Ảnh cũng xong ➔ Tự động kích hoạt `/assemble`. |
| **`IMAGES_COMPLETED`** | VPS Linux Playwright | 100% Ảnh Keyframes 4K đã tải về đạt GK5 và upload lên GDrive. | Lưu trạng thái Ảnh sẵn sàng; nếu Audio cũng xong ➔ Tự động kích hoạt `/assemble`. |
| **`GK6_VERIFIED`** | GitHub Actions (Assembly) | Đã kiểm toán đầy đủ 15 audio parts và $\ge 15$ ảnh keyframes trước khi dựng. | Cập nhật thanh tiến trình realtime trên WebApp Dashboard. |
| **`ASSEMBLY_COMPLETED`** | GitHub Actions (Assembly) | Video Master MP4 90 phút đã render xong, đạt GK7 và đã upload lên GDrive. | Đổi trạng thái Sheet sang **`Done`**, thông báo thành công lên WebApp/Telegram! |
| **`GK_ERROR`** | Mọi Chốt Chặn | Phát hiện vi phạm chất lượng tại một bước cụ thể. | Ghi log cảnh báo và thông báo lỗi kèm vị trí Part cần xử lý. |

---

## 🚀 7. Hướng Dẫn Vận Hành Thực Tế

1. **Khởi chạy Ý tưởng (Ideation & Scripting)**:
   * Truy cập WebApp Control Center tại `https://historysnooze-gateway.hothihuong113.workers.dev`.
   * Gợi ý Tiêu đề ➔ Chọn Nhân vật ➔ Hệ thống tự động biên kịch 15 tập (GK1, GK2, GK3) trên Cloudflare Edge.
2. **Sinh Âm Thanh (Voiceover)**:
   * Bấm `/mediagen` ➔ GitHub Actions kích hoạt ma trận 15 máy ảo từ Cache (GK4) ➔ Tự động bắn tín hiệu `VOICEOVER_COMPLETED` về Cloudflare.
3. **Sinh Ảnh (ImageFX)**:
   * Bấm `/imagegen` ➔ VPS Linux điều khiển Chrome CDP 9222 sinh ảnh 4K (GK5) ➔ Tự động bắn tín hiệu `IMAGES_COMPLETED` về Cloudflare.
4. **Dựng Phim Hoàn Tất (Assembly)**:
   * Cloudflare tự động dispatch `/assemble` ➔ GitHub Actions kéo nguyên liệu từ GDrive, kiểm toán GK6, dựng video Part-by-Part và kiểm toán GK7 ➔ Upload Master MP4 lên Google Drive `03.Final Production/` và đổi Sheet sang `Done`!

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
