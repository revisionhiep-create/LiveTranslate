"""Legacy compatibility module: Anime-Whisper is superseded by Kotoba-Whisper v2.0 (faster-whisper)."""

from asr_kotoba_whisper import KotobaWhisperEngine as AnimeWhisperEngine, MODEL_ID

__all__ = ["AnimeWhisperEngine", "MODEL_ID"]
