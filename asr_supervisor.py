"""ASR worker process lifecycle, health monitoring, and memory supervisor.

Handles spawning and readiness checks for isolated ASR worker processes,
memory usage tracking (process RSS and GPU allocations), and cache purging.
"""

import gc
import logging
from typing import Any, Dict, Optional

import psutil
import torch

from asr_client import ASRClient

log = logging.getLogger("LiveTranslate.Supervisor")


def load_asr_client(worker_config: Dict[str, Any]) -> ASRClient:
    """Spawn and wait for a dedicated ASR worker process to become ready."""
    # request_timeout bounds how long a hung worker can stall the realtime path
    # before it is killed and auto-restarted.
    client = ASRClient(worker_config, request_timeout=60.0)
    try:
        client.start()
        client.wait_ready()
        return client
    except Exception:
        client.shutdown()
        raise


def load_engine_client(config: Dict[str, Any]) -> Any:
    """Build the ASR backend for a worker config.
    
    Local engines run in an isolated worker subprocess (ASRClient);
    remote-whisper is an in-process HTTP client.
    """
    if config.get("engine_type") == "remote-whisper":
        from asr_remote import RemoteASREngine

        url = config.get("remote_asr_url") or "http://127.0.0.1:8765"
        engine = RemoteASREngine(server_url=url)
        language = config.get("language")
        if language:
            engine.set_language(language)
        return engine
    return load_asr_client(config)


def release_memory_caches() -> None:
    """Trigger Python garbage collection and release unused CUDA memory caches."""
    gc.collect()
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def take_mem_snapshot(
    main_proc: psutil.Process,
    asr_client: Optional[Any] = None,
    overlay: Optional[Any] = None,
    vad: Optional[Any] = None,
) -> Dict[str, Any]:
    """Capture a snapshot of host RAM (main + worker), GPU VRAM, and queue buffer depths."""
    rss_mb = main_proc.memory_info().rss / 1024 / 1024
    worker_rss_mb = 0.0

    if asr_client is not None and getattr(asr_client, "pid", None) is not None:
        try:
            worker_rss_mb = psutil.Process(asr_client.pid).memory_info().rss / 1024 / 1024
        except Exception:
            worker_rss_mb = 0.0

    gpu_alloc_mb = 0.0
    gpu_reserved_mb = 0.0
    try:
        if torch.cuda.is_available():
            gpu_alloc_mb = torch.cuda.memory_allocated() / 1024 / 1024
            gpu_reserved_mb = torch.cuda.memory_reserved() / 1024 / 1024
    except Exception:
        pass

    msgs = len(overlay._messages) if overlay and hasattr(overlay, "_messages") else 0
    vad_buf = len(vad._speech_buffer) if vad and hasattr(vad, "_speech_buffer") else 0

    return {
        "rss": rss_mb,
        "worker_rss": worker_rss_mb,
        "total_rss": rss_mb + worker_rss_mb,
        "gpu_alloc": gpu_alloc_mb,
        "gpu_reserved": gpu_reserved_mb,
        "msgs": msgs,
        "vad_buf": vad_buf,
    }

