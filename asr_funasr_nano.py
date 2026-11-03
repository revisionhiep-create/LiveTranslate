import logging
import os
import sys
import re
from typing import Optional, Dict, Any
import numpy as np
import torch

log = logging.getLogger("LiveTranslate.FunASR-Nano")

# Add bundled code to path so model.py can resolve its imports (ctc, tools.utils)
_NANO_DIR = os.path.join(os.path.dirname(__file__), "funasr_nano")


class FunASRNanoEngine:
    """Speech-to-text using Fun-ASR-Nano-2512 or Fun-ASR-MLT-Nano-2512 in memory."""

    def __init__(
        self,
        device: str = "cuda",
        hub: str = "ms",
        engine_type: str = "funasr-nano",
    ) -> None:
        if _NANO_DIR not in sys.path:
            sys.path.insert(0, _NANO_DIR)

        # Pre-register FunASRNano model class before AutoModel looks it up
        try:
            from funasr_nano import model as _nano_model  # noqa: F401
        except ImportError:
            import model as _nano_model  # type: ignore # noqa: F401
        sys.modules.setdefault("model", _nano_model)

        from funasr import AutoModel
        from model_manager import (
            ASR_MODEL_IDS,
            ensure_qwen_weights,
            get_local_model_path,
            neutralize_funasr_requirements,
        )

        model_name = ASR_MODEL_IDS[engine_type]
        local = get_local_model_path(engine_type, hub=hub)
        model = local or model_name

        if local:
            # Safety net; the download flow normally fetches these up-front.
            ensure_qwen_weights(local, hub=hub)
            neutralize_funasr_requirements(local)

        prev_cwd = os.getcwd()
        if local:
            os.chdir(local)
        try:
            self._model = AutoModel(
                model=model,
                trust_remote_code=True,
                device=device,
                hub=hub,
                disable_update=True,
            )
        finally:
            os.chdir(prev_cwd)
        self.language: Optional[str] = None
        log.info(f"{engine_type} loaded: {model_name} on {device} (hub={hub})")

    def set_language(self, language: str) -> None:
        old = self.language
        self.language = language if language != "auto" else None
        log.info(f"Fun-ASR-Nano language: {old} -> {self.language}")

    def unload(self) -> None:
        if hasattr(self, "_model") and self._model is not None:
            try:
                self._model.model.to("cpu")
            except Exception:
                pass
            self._model = None

    def transcribe(self, audio: np.ndarray) -> Optional[Dict[str, Any]]:
        """Transcribe audio segment (float32, 16kHz mono) in-memory without disk I/O."""
        if audio is None or len(audio) == 0:
            return None

        tensor_audio = torch.from_numpy(audio).float()
        kwargs: Dict[str, Any] = {
            "input": [tensor_audio],
            "batch_size": 1,
            "disable_pbar": True,
        }
        if self.language:
            kwargs["language"] = self.language

        with torch.inference_mode():
            result = self._model.generate(**kwargs)

        if not result or not result[0].get("text"):
            return None

        # "text" keeps punctuation; "text_tn" strips it all via regex
        text = result[0]["text"]

        # Clean special tags
        text = re.sub(r"<\|[^|]+\|>", "", text).strip()

        if not text or text == "sil":
            return None

        detected_lang = self.language or self._guess_language(text)

        log.debug(f"ASR: {text}")
        return {
            "text": text,
            "language": detected_lang,
            "language_name": detected_lang,
        }

    def _guess_language(self, text: str) -> str:
        cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        jp = sum(
            1 for c in text if "\u3040" <= c <= "\u30ff" or "\u31f0" <= c <= "\u31ff"
        )
        ko = sum(1 for c in text if "\uac00" <= c <= "\ud7af")
        total = len(text)
        if total == 0:
            return "auto"
        if jp > 0:
            return "ja"
        if ko > total * 0.3:
            return "ko"
        if cjk > total * 0.3:
            return "zh"
        return "en"
