import logging
import numpy as np

log = logging.getLogger("LiveTranslate.KotobaWhisper")

MODEL_ID = "kotoba-tech/kotoba-whisper-v2.0-faster"


class KotobaWhisperEngine:
    """Speech-to-text using kotoba-tech/kotoba-whisper-v2.0-faster via faster-whisper (CTranslate2).

    Japanese-specialized Whisper model with native CTranslate2 acceleration.
    2-3x faster than original Anime-Whisper with lower hallucination rate.
    """

    def __init__(self, device="cuda", hub="hf", pad_seconds=0.5):
        from asr_engine import ASREngine
        from model_manager import get_local_model_path, MODELS_DIR

        local = get_local_model_path("kotoba-whisper", hub=hub)
        model_size_or_path = local or MODEL_ID

        parsed_device = "cuda" if device.startswith("cuda") else "cpu"
        device_index = 0
        if ":" in device and parsed_device == "cuda":
            try:
                device_index = int(device.split(":")[1])
            except ValueError:
                pass

        download_root = str((MODELS_DIR / "huggingface" / "hub").resolve())

        self._engine = ASREngine(
            model_size=model_size_or_path,
            device=parsed_device,
            device_index=device_index,
            compute_type="float16" if parsed_device == "cuda" else "int8",
            language="ja",
            download_root=download_root,
            pad_seconds=pad_seconds,
        )
        self.language = "ja"
        log.info(f"KotobaWhisper loaded from {model_size_or_path} on {device}")

    def set_language(self, language: str):
        self.language = "ja"
        if hasattr(self, "_engine") and self._engine is not None:
            self._engine.set_language("ja")

    def set_input_padding(self, pad_seconds):
        if hasattr(self, "_engine") and self._engine is not None:
            self._engine.set_input_padding(pad_seconds)

    def unload(self):
        if hasattr(self, "_engine") and self._engine is not None:
            self._engine.unload()
            self._engine = None

    def transcribe(self, audio: np.ndarray) -> dict | None:
        if not hasattr(self, "_engine") or self._engine is None:
            return None
        return self._engine.transcribe(audio)


# Backward compatibility alias
AnimeWhisperEngine = KotobaWhisperEngine
