# Coding Best Practices & Engineering Guidelines

This document serves as the persistent knowledge base for real-time audio capture, Voice Activity Detection (VAD), Automatic Speech Recognition (ASR), and low-latency Machine Translation (MT) systems.

---

## 🐍 Python (.py) Architecture & Performance Patterns

### 1. Audio Capture & WASAPI Streaming (PortAudio / PyAudio)
* **Never Re-instantiate `PyAudio()` in Loops:** 
  - Instantiating and terminating `pyaudio.PyAudio()` initializes and uninitializes the PortAudio library and Windows Audio Session API (WASAPI) COM interfaces. Doing this periodically (e.g. to poll default devices) induces 50–200ms latency spikes, driver deadlocks, and buffer overruns.
  - *Pattern:* Keep a single `PyAudio` session for the application lifecycle. Query device changes via OS notification events or lightweight Win32 API checks, never by tearing down the subsystem.
* **Zero-Copy & Memory Reuse in Ingest Buffers:**
  - Avoid `np.concatenate` in hot loops (e.g., every 32ms chunk). It repeatedly reallocates contiguous heap memory and stresses the Python garbage collector.
  - *Pattern:* Use pre-allocated ring buffers (`collections.deque(maxlen=N)` or fixed-size preallocated NumPy arrays with write pointers) for audio chunks.
* **Non-blocking Resampling:**
  - Cache linear interpolation index weights by chunk length to avoid re-generating interpolation grids per frame.

### 2. Voice Activity Detection (Silero VAD v5)
* **Exact Window Quantum:**
  - Silero VAD v5 strictly requires **512 samples at 16kHz** (32ms). Irregular chunk sizes degrade model accuracy.
* **State Management:**
  - Silero VAD is stateful. Preserve hidden states across consecutive streaming chunks.
  - Call `model.reset_states()` **only** on stream initialization, after explicit pipeline pauses, or after prolonged silence (> 5 seconds). Do not reset states between speech segments of the same session.
* **Onset Buffering & Tail Padding:**
  - **Pre-speech Buffer (Onset):** Maintain ~96–128ms (3–4 chunks) in a circular buffer to capture soft initial consonants (e.g., /s/, /t/, /k/) before VAD confidence crosses the trigger threshold.
  - **Speech Tail Padding:** When silence is detected, include at least 150–300ms of trailing audio buffer before cutting. In languages like Japanese, sentence-final particles (`ね`, `よ`, `か`) and trailing verb inflections (`〜でした`, `〜ます`) naturally decay in energy and will be chopped off without adequate tail-padding.

### 3. Real-Time ASR & Multiprocessing Worker Isolation
* **Dedicated Worker Isolation (`multiprocessing.Process`):**
  - CTranslate2 (`faster-whisper`) and PyTorch release the GIL during matrix computations, but Python interop, tokenizer allocations, and CUDA synchronization can block the main GUI thread.
  - Running ASR in an isolated spawned process guarantees that GUI event loops (PyQt6/PySide) and audio capture threads maintain 60 FPS and zero frame drops.
* **In-Memory Audio Passing (Zero Disk I/O):**
  - Never write intermediate audio to disk via `tempfile.mktemp()` or `.wav` files. Pass raw float32 NumPy arrays directly across IPC pipes (`Connection.send_bytes` or serialized NumPy ndarrays).
* **Local Agreement Streaming (UFAL SimulStreaming Pattern):**
  - For continuous/interim recognition, decode rolling audio and commit tokens only when they match across consecutive inference passes ($k \ge 2$). Trim audio strictly up to the boundary of committed text.

### 4. Japanese-to-English Low-Latency Streaming Translation
* **SOV vs. SVO Head-Final Inversion:**
  - Japanese places verbs and negation at the end of clauses (`〜ない`, `〜てはいけない`). Translating before the clause boundary forces hallucinations or retroactive corrections.
* **Context Continuity (Pro-Drop Resolution):**
  - Japanese conversations frequently omit pronouns (I/you/he/she). Streaming translators must maintain a sliding conversation context buffer:
    ```markdown
    Source: <recent source 1>
    Translation: <recent translation 1>
    Source: <recent source 2>
    Translation: <recent translation 2>
    ```
    This ensures subsequent clauses correctly resolve pronoun references instead of defaulting to erratic pronouns.
* **Prompt Optimization for Low Latency:**
  - Explicitly disable model thinking/reasoning modes (`enable_thinking: false`, `reasoning_effort: "none"`) in real-time translation workloads to avoid burning the token budget and delaying the first token (TTFT).

### 5. Code Hygiene & Concurrency
* **Replace Deprecated Standard Library APIs:**
  - Avoid `locale.getdefaultlocale()` (slated for removal in Python 3.15). Use `locale.getlocale()[0]` or `locale.getencoding()`.
* **Lock Granularity:**
  - Never execute blocking IPC calls or heavy inference while holding state locks (e.g., `_vad_lock`). Minimize critical sections to pointer updates and queue handoffs.

### 6. Whisper Silence & Outro Hallucination Suppression
* **Root Cause:**
  - Whisper models (including `large-v3`, `large-v3-turbo`, and distilled variants like `kotoba-whisper`) were trained on large volumes of YouTube/web videos. Audio segments with faint background music, room reverb, or silence decode to the language model's strongest training priors: YouTube outro lines like `ご視聴ありがとうございました` ("Thank you for watching") or `チャンネル登録よろしくお願いします`.
* **Two-Tier Mitigation Strategy:**
  1. **Confidence Thresholding (`no_speech_prob`):** In `faster-whisper`, inspect each `Segment.no_speech_prob`. Segments with `no_speech_prob > 0.7` represent low-energy silence/noise and should be pruned prior to text assembly.
  2. **Normalized Hallucination Filtering:** Run text normalization (stripping all punctuation, symbols, whitespace, and quotes) and evaluate against signature outro artifacts (`is_whisper_hallucination()`). Apply this check at both the ASR engine level and downstream pipeline dispatch points (`_process_segment`, `_process_segment_text`, `_process_interim_final`, `_do_interim_asr`) so silence artifacts never hit the translation LLM or subtitle overlay.

---

## 🌐 JavaScript & TypeScript (.js / .ts) Streaming & UI Best Practices

### 1. Web Audio API & Ingest Pipelines
* **AudioWorklet over ScriptProcessorNode:**
  - `ScriptProcessorNode` runs on the main browser UI thread and causes audio dropouts during DOM reflows. Always capture and downsample audio inside an `AudioWorkletProcessor` running on the high-priority Web Audio rendering thread.
* **Transferable Objects for IPC:**
  - When posting audio PCM chunks from an `AudioWorklet` to the main thread or a Web Worker, pass the underlying `ArrayBuffer` in the transfer list (`postMessage(msg, [msg.buffer])`) for zero-copy memory transfers.

### 2. High-Frequency UI Updates & Subtitle Rendering
* **`requestAnimationFrame` Throttling:**
  - Streaming translation tokens arrive at high frequencies (up to 30–50 tokens/sec). Directly triggering React state updates or DOM mutations on every token degrades frame rates.
  - *Pattern:* Accumulate incoming tokens in a mutable buffer and flush to DOM/Canvas on `requestAnimationFrame` boundaries.
* **Hardware-Accelerated CSS for Overlays:**
  - Use `transform: translate3d()` and `will-change: transform` for smooth dragging and subtitle animations. Avoid animating layout properties (`top`, `left`, `margin`) to prevent layout thrashing.

