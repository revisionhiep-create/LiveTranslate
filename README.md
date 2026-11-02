# LiveTranslate

<div align="center">

<img src="icon.ico" width="128" height="128" alt="LiveTranslate Icon" />

### Real-Time Live Stream Subtitle Translator for Windows

**Watch foreign livestreams, VTubers, anime, and games with instant, local, zero-latency subtitles.**

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078d4?logo=windows)](https://github.com/revisionhiep-create/LiveTranslate)
[![Python](https://img.shields.io/badge/Python-3.10%20--%203.12-3776AB?logo=python)](https://github.com/revisionhiep-create/LiveTranslate)
[![CUDA](https://img.shields.io/badge/CUDA-12.6%20%7C%2012.8%20(RTX%2050xx)-76B900?logo=nvidia)](https://github.com/revisionhiep-create/LiveTranslate)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

[English](README.md) | [中文说明](README_zh.md)

</div>

---

## 🌟 About This Fork

While the original LiveTranslate upstream was designed with stream broadcasting tools (like OBS) in mind, this fork is specifically optimized for **viewers watching foreign livestreams** (YouTube, Twitch, TwitCasting, Kick, etc.), anime, galgames, and voice chat on **Windows**.

### What's New & Improved in This Fork:
- 🚀 **Zero-Config First Launch**: Defaults to **Kotoba-Whisper v2.0** (`kotoba-tech/kotoba-whisper-v2.0-faster`) with native CTranslate2 acceleration, alongside a built-in **Qwen3.5-4B** local translator. Works right out of the box with **no API keys, no LM Studio, and no external software required**!
- 🎙️ **Next-Gen Voice Capture Engines**:
  - **Kotoba-Whisper v2.0**: Native CTranslate2 Japanese model (2-3x faster than legacy anime-whisper, lower hallucination rate, optimized for JP speech & anime banter).
  - **Whisper Large-v3 Turbo**: 4-layer decoder high-speed conversational model, handles overlapping stream audio and gaming background music significantly better than base V2/V3.
  - **SenseVoice Small**: Non-autoregressive single-pass ASR (~70ms latency), completely immune to repetitive hallucination loops.
- ⚡ **No-Thinking Subtitle Streaming**: The local Qwen translation engine explicitly loads with reasoning mode suppressed (`enable_thinking=False`), guaranteeing instantaneous character-by-character translation without wasting tokens or latency on hidden `<think>` reasoning blocks.
- 🖥️ **Multi-Monitor Scaling Bug Fix**: Moving the overlay between monitors with different display resolutions and DPI scaling factors now scales and renders cleanly without clipping or stretching.
- 💾 **Full Settings & Language Persistence**: Remembers your chosen target and source languages (no longer forcing Chinese defaults), window coordinates, and toggle states (`Top-most`, `Click-through`, `Auto-scroll`).
- 📺 **Dual Subtitle Windows with Position Memory**: Includes both the main control/history overlay and a secondary lightweight transparent subtitle strip designed to sit directly under video players. Middle-click and drag anywhere; positions are automatically saved across sessions.
- 🐱 **Single-Instance GUI Launcher (`LiveTranslate.exe`)**: One clean icon on your taskbar. Automatically prompts to install dependencies if missing, bypassing confusing console errors and intrusive first-launch dialogs.
- 🏎️ **Optimized Audio & VAD Pipeline**: High-performance vectorized RMS computation, 8.9x faster audio downmixing, resampler caching, and energy-based speech detection tuned for fast stream dialogue.

---

## 📸 Screenshots & UI

```
┌────────────────────────────────────────────────────────────────────────┐
│ [≡] LiveTranslate           [Hide] [Sub] [Run] [Clear] [Settings] [Quit]│
│ [ ] Click-through  [x] Top-most  [x] Auto-scroll                       │
│ Model: qwen3.5-4b    Source: ja - 日本語         Target: en - English   │
├────────────────────────────────────────────────────────────────────────┤
│ RMS: 25% | VAD: 100% | Kotoba-Whisper [cuda:0] | ASR 58ms TL 180ms      │
│                                                                        │
│ [08:24:20] [ja] なにこれ、おもしろいじゃん ASR 68ms                      │
│ > What is this, it's hilarious! TL 209ms                               │
│                                                                        │
│ [08:24:29] [ja] えっ、これもできるの？マジ？ ASR 61ms                    │
│ > Wow, I can do that too? For real? TL 237ms                           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start (Windows)

### Requirements
- **OS**: Windows 10 / 11 (64-bit)
- **GPU**: NVIDIA GeForce RTX (RTX 30xx, 40xx, or 50xx with 6+ GB VRAM recommended for local Whisper + Qwen models)
- **Audio**: Any standard Windows audio output (WASAPI loopback captures whatever you hear in your browser, Discord, or media player)

### One-Click Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/revisionhiep-create/LiveTranslate.git
   cd LiveTranslate
   ```

2. **Launch `LiveTranslate.exe`** (or double-click `install.bat`):
   - If launching for the first time, `LiveTranslate.exe` will detect that dependencies need to be installed and ask if you'd like to set them up.
   - Click **Yes** — it automatically creates the virtual environment, configures the proper PyTorch build for your NVIDIA GPU (including CUDA 12.8 for RTX 50-series Blackwell GPUs), and verifies all libraries.

3. **First-Run Model Download**:
   - The setup dialog will automatically download **Kotoba-Whisper v2.0** and **Qwen3.5-4B** from Hugging Face.
   - Once completed, the subtitle overlay appears and starts translating your system audio in real-time!

---

## 🧠 Translation Modes

### 1. Built-in Local Qwen3.5-4B (Default — No Software or API Key Needed)
By default, LiveTranslate uses an integrated **Qwen3.5-4B** translator running directly on your GPU/CPU via Hugging Face `transformers`.
- Fast, private, and 100% offline.
- Thinking mode is suppressed so translations stream token-by-token immediately.
- To use, simply leave **"Use built-in Qwen3.5-4B"** checked under **Settings → Translation**.

---

### 2. Using LM Studio (Optional)

If you already use [LM Studio](https://lmstudio.ai/) and prefer running other models (e.g., Llama 3, Command-R, Mistral, Gemma, or custom GGUFs):

1. **In LM Studio**:
   - Download your preferred translation model.
   - Go to the **Developer / Local Server** tab (`<->`).
   - Select your model and click **Start Server** (default address: `http://localhost:1234`).
2. **In LiveTranslate**:
   - Open **Settings (gear icon) → Translation tab**.
   - **Uncheck** *"Use built-in Qwen3.5-4B"*.
   - In **Model Configurations**, click **Add** or **Edit**:
     - **Name**: `LM Studio`
     - **API Base**: `http://127.0.0.1:1234/v1`
     - **API Key**: `lm-studio` (can be any string)
     - **Model**: Enter your loaded model's identifier (or leave as displayed in LM Studio).
   - Click **Save**. LiveTranslate will now stream translations through your LM Studio server!

---

### 3. Using Cloud API Keys (OpenAI, DeepSeek, Grok, etc.)

For lightweight GPU usage, you can offload translation to external cloud providers:

1. Open **Settings → Translation tab**.
2. **Uncheck** *"Use built-in Qwen3.5-4B"*.
3. Click **Add** or **Edit** in Model Configurations:
   - **DeepSeek**:
     - API Base: `https://api.deepseek.com/v1`
     - API Key: `sk-your-deepseek-key`
     - Model: `deepseek-chat`
   - **OpenAI**:
     - API Base: `https://api.openai.com/v1`
     - API Key: `sk-your-openai-key`
     - Model: `gpt-4o-mini`
4. Click **Save**.

---

## 🎮 Overlay Controls & Hotkeys

| Control | Action |
|---------|--------|
| **Top Left Drag Bar** | Click and drag with Left Mouse Button to move the main overlay window. |
| **Subtitle Button (`Sub`)** | Toggles the secondary floating subtitle window. |
| **Middle-Click on Subtitles** | Drag the secondary subtitle strip directly under your YouTube / Twitch video player. Position is automatically remembered! |
| **`Top-most` Checkbox** | Keeps subtitles pinned on top of browser windows or games. |
| **`Click-through` Checkbox** | Allows mouse clicks to pass directly through the subtitle text to the window behind it. |
| **`Auto-scroll` Checkbox** | Automatically scrolls the transcript history to the newest line. |
| **Source / Target Combos** | Quickly switch recognized language (default `ja`) and translated target (default `en`). |

---

## 🎯 Recommended Settings for Watching Japanese Streamers

To achieve maximum transcription accuracy, minimal latency, and zero background music false-triggers when watching Japanese VTubers (Hololive, Nijisanji, VSPO!), Twitch/YouTube livestreams, anime, or gaming broadcasts, use the following settings:

### 1. VAD & Audio Segmentation Tuning (**Settings → AD / ASR**)

| Setting | Recommended Value | Optimization Purpose |
|:---|:---:|:---|
| **VAD Mode** | `Energy-based` | Prevents quiet stream background music (BGM) and game sounds from falsely triggering speech recognition. |
| **Silero VAD Threshold** | `30%` (`0.30`) | Accurately distinguishes human speech from background breathing, mechanical keyboard clicks, and quiet mic hiss. |
| **Energy Threshold (for Energy-based mode)** | `25‰` (`0.025`) | Sets a volume floor to filter out faint stream ambiance while reliably picking up the streamer's voice. |
| **Min speech** | `0.40 s` | Catches fast Japanese interjections, reaction noises, and short slang (e.g., 「うん」「はい」「えっ」「草」「やば」). |
| **Max speech** | `8.00 s` | Prevents runaway sentences during rapid talking; cuts long speech into clean, readable subtitle segments. |
| **Silence** | `Fixed` | Provides predictable, consistent sentence boundary slicing. |
| **Silence dur** | `0.50 s` | Sends audio to ASR within 0.5s of the streamer pausing, ensuring snappy real-time translation with minimal delay. |
| **Incremental ASR** | `Unchecked` (Off) | Disables interim partial transcriptions, eliminating distracting jittery subtitle flashes and saving GPU compute for final output. |
| **Interim interval** | `2.00 s` | Default setting when Incremental ASR is disabled. |

---

### 2. Recommended Engine & Display Pairings

| Component | Recommended Choice | Advantage |
|:---|:---|:---|
| **Voice Capture (ASR)** | **`[Accurate] Kotoba-Whisper v2.0 (faster-whisper, ja)`** *(Default)*<br>*(or **Whisper Large-v3 Turbo** for heavy BGM)* | 2–3× faster inference with native CTranslate2 acceleration; fine-tuned specifically on conversational Japanese and anime banter. |
| **Source Language** | `ja - Japanese` | Direct Japanese acoustic modeling with lowest hallucination rate. |
| **Target Language** | `en - English` (or your preferred language) | Seamlessly translated by the built-in local Qwen3.5-4B model. |
| **Translation Engine** | **Built-in Qwen3.5-4B** (Local) | Zero setup, completely offline, with thinking mode suppressed (`enable_thinking=False`) for instant token-by-token streaming. |
| **Subtitle Window** | Floating Subtitle Bar (`Sub` button) | Middle-click and drag the sleek subtitle strip directly beneath your video player. Position and dimensions are remembered across restarts! |

---

## 🏗️ Architecture

```
System Audio (WASAPI Loopback 16 kHz)
   │
   ├──> Vectorized Energy & Silero VAD (32ms frames)
   │       │
   │       └──> Speech Segment Collector
   │               │
   │               ├──> Kotoba-Whisper v2.0 / Large-v3-Turbo / SenseVoice (ASR Process)
   │               │       │
   │               │       └──> Recognized Text (e.g. Japanese)
   │               │
   │               └──> Local Qwen3.5-4B (No-Thinking Mode) or Cloud LLM API
   │                       │
   │                       └──> Streamed Translation (e.g. English)
   │
   └──> Multi-Monitor DPI Scaled Transparent PyQt6 Overlay + Subtitle Window
```

---

## 🧪 Testing & Verification

Run the comprehensive unit test suite:
```bash
.venv\Scripts\pytest.exe
```
```text
======================= 56 passed in 3.10s =======================
```

---

## 📄 License & Credits

- Based on the open-source [LiveTranslate](https://github.com/TheDeathDragon/LiveTranslate) architecture.
- Japanese speech recognition powered by [Kotoba-Whisper v2.0](https://huggingface.co/kotoba-tech/kotoba-whisper-v2.0-faster) by Kotoba Technologies, [Whisper Large-v3 Turbo](https://huggingface.co/deepdml/faster-whisper-large-v3-turbo-ct2), and [SenseVoice Small](https://huggingface.co/FunAudioLLM/SenseVoiceSmall) by FunAudioLLM.
- Voice activity detection by [Silero VAD](https://github.com/snakers4/silero-vad).
- Local LLM inference via [Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) by Alibaba Cloud Qwen Team.
- Distributed under the [MIT License](LICENSE).
