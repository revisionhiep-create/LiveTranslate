"""Text segmentation and utterance processing for streaming ASR.

Provides sentence boundary splitting via yasbd (pysbd adapter), comma-based
fallbacks for run-on speech, echo overlap suppression, short utterance
filtering, and Whisper silence/outro hallucination filtering.
"""

import logging
import re
from typing import Dict, List, Optional
from yasbd import get_supported_langs, pysbd_adapter

log = logging.getLogger("LiveTranslate.Segmenter")

_segmenter_cache: Dict[str, pysbd_adapter.Segmenter] = {}

# Known silence/BGM hallucination artifacts from Whisper's YouTube training data
_HALLUCINATION_PATTERNS = (
    # Japanese YouTube outro / silence artifacts
    "ご視聴ありがとうございました",
    "ご視聴ありがとうございまし",
    "ご視聴ありがとう",
    "ご視聴いただきありがとうございました",
    "ご視聴いただき誠にありがとうございました",
    "ご視聴誠にありがとうございました",
    "ご視聴いただきありがとう",
    "ご視聴いただき",
    "最後までご視聴いただきありがとうございました",
    "最後までご視聴ありがとうございました",
    "最後までご視聴",
    "視聴ありがとうございました",
    "ご清聴ありがとうございました",
    "ご清聴いただきありがとうございました",
    "チャンネル登録よろしくお願いします",
    "チャンネル登録よろしくお願いいたします",
    "チャンネル登録よろしく",
    "チャンネル登録お願い",
    "高評価チャンネル登録",
    "高評価とチャンネル登録",
    "グッドボタンチャンネル登録",
    "高評価よろしくお願いします",
    # English YouTube outro / silence artifacts
    "thank you for watching",
    "thanks for watching",
    "thank you so much for watching",
    "please subscribe",
    "subscribe to my channel",
    "like and subscribe",
    "please like and subscribe",
    "don't forget to subscribe",
    "don't forget to like and subscribe",
    "see you in the next video",
    "see you next time",
    "subtitles by",
    "subtitled by",
    "amara.org",
    # Chinese YouTube outro / silence artifacts
    "谢谢观看",
    "謝謝觀看",
    "感谢观看",
    "感謝觀看",
    "感谢您的观看",
    "感謝您的觀看",
    "请订阅我的频道",
    "請訂閱我的頻道",
    "欢迎订阅",
    "歡迎訂閱",
    "别忘了点赞和订阅",
    "別忘了點贊和訂閱",
)


def is_whisper_hallucination(text: str) -> bool:
    """Return True if text matches known Whisper YouTube outro/silence hallucination artifacts."""
    if not text or not text.strip():
        return False

    # Normalize by stripping punctuation, symbols, quotes, and whitespace
    clean = re.sub(
        r"[\s\.,!\?。！？、〜～\-_/\\:;：；'\"`『』「」〈〉《》【】\[\]\(\)]",
        "",
        text,
    ).lower()
    if not clean:
        return False

    for pat in _HALLUCINATION_PATTERNS:
        clean_pat = re.sub(
            r"[\s\.,!\?。！？、〜～\-_/\\:;：；'\"`『』「」〈〉《》【】\[\]\(\)]",
            "",
            pat,
        ).lower()
        if clean_pat and clean_pat in clean:
            return True

    return False


def get_segmenter(lang: str) -> pysbd_adapter.Segmenter:
    """Return a cached sentence segmenter for the given language (fallback to 'en')."""
    if lang not in _segmenter_cache:
        supported = get_supported_langs()
        seg_lang = lang if lang in supported else "en"
        _segmenter_cache[lang] = pysbd_adapter.Segmenter(language=seg_lang, clean=False)
    return _segmenter_cache[lang]


def split_sentences(text: str, lang: str = "en") -> List[str]:
    """Split text into sentences using yasbd, with comma fallback for long text."""
    if not text or not text.strip():
        return []

    seg = get_segmenter(lang)
    parts = [p.strip() for p in seg.segment(text) if p.strip()]
    if len(parts) > 1:
        return parts

    # Comma fallback for long unsplit text — split at last balanced comma
    # CJK 「、」at 25 chars; all commas at 60 chars (long sentence, reduce latency)
    min_len = 25 if any(c == "、" for c in text) else 60
    if len(text) > min_len:
        for i in range(len(text) - 8, 5, -1):
            if text[i] in ",，;；、":
                before = text[: i + 1].strip()
                after = text[i + 1 :].strip()
                if before and after and len(before) > 15 and len(after) > 3:
                    return [before, after]

    return parts


def is_short_utterance(text: str) -> bool:
    """Check if text has <= 8 alphanumeric chars (likely noise/filler/fragment)."""
    alnum = sum(1 for c in text if c.isalnum())
    return alnum <= 8


def strip_committed_overlap(text: str, committed_tail: str) -> str:
    """Remove text that overlaps with previously committed content (echo suppression)."""
    if not committed_tail or not text:
        return text

    tail = committed_tail.lower().rstrip()
    text_lower = text.lower()
    max_check = min(len(tail), len(text_lower))
    for overlap_len in range(max_check, 2, -1):
        if text_lower[:overlap_len] == tail[-overlap_len:]:
            stripped = text[overlap_len:].strip()
            if stripped:
                log.debug(
                    f"Stripped echo overlap ({overlap_len} chars): '{text[:overlap_len]}...'"
                )
                return stripped
            return ""
    return text
