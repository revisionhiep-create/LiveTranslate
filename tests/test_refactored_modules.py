"""Unit tests for refactored modular subsystems: text_segmenter, asr_supervisor,
LocalQwenTranslator context window, AudioCapture deque mixing, and VADProcessor deque.
"""

import unittest
from unittest.mock import MagicMock
import numpy as np

import text_segmenter
import asr_supervisor
from audio_capture import AudioCapture
from vad_processor import VADProcessor
from translator import LocalQwenTranslator


class TestRefactoredModules(unittest.TestCase):
    def test_text_segmenter_split_and_fallback(self):
        parts = text_segmenter.split_sentences("Hello world. How are you today?", lang="en")
        self.assertEqual(parts, ["Hello world.", "How are you today?"])

        # Test comma fallback for long unsplit text (>60 chars)
        long_text = "This is a very long run-on sentence without periods, but it contains a comma separator that should be split."
        split_parts = text_segmenter.split_sentences(long_text, lang="en")
        self.assertGreaterEqual(len(split_parts), 2)

    def test_text_segmenter_short_utterance(self):
        self.assertTrue(text_segmenter.is_short_utterance("hi!"))
        self.assertTrue(text_segmenter.is_short_utterance("yeah"))
        self.assertFalse(text_segmenter.is_short_utterance("This is a complete sentence."))

    def test_text_segmenter_echo_suppression(self):
        tail = "and we went to the market"
        incoming = "market and bought some fruit"
        stripped = text_segmenter.strip_committed_overlap(incoming, tail)
        self.assertEqual(stripped, "and bought some fruit")

    def test_asr_supervisor_mem_snapshot(self):
        mock_proc = MagicMock()
        mock_proc.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        snap = asr_supervisor.take_mem_snapshot(mock_proc)
        self.assertEqual(snap["rss"], 100.0)
        self.assertIn("total_rss", snap)
        self.assertIn("gpu_alloc", snap)

    def test_audio_capture_drain_mic_samples(self):
        ac = AudioCapture()
        # Feed 2 chunks of 100 samples each
        chunk1 = np.ones(100, dtype=np.float32)
        chunk2 = np.ones(100, dtype=np.float32) * 2
        ac._mic_chunks.append(chunk1)
        ac._mic_chunks.append(chunk2)

        # Drain 150 samples: should take all 100 of chunk1 and 50 of chunk2
        drained, rms = ac._drain_mic_samples(150)
        self.assertEqual(len(drained), 150)
        np.testing.assert_array_equal(drained[:100], 1.0)
        np.testing.assert_array_equal(drained[100:], 2.0)
        self.assertGreater(rms, 0)
        # Remainder in deque should have 50 samples left
        self.assertEqual(len(ac._mic_chunks[0]), 50)

    def test_vad_processor_deque_trim_front(self):
        vad = VADProcessor(sample_rate=16000)
        c1 = np.ones(160, dtype=np.float32)
        c2 = np.ones(160, dtype=np.float32) * 2
        c3 = np.ones(160, dtype=np.float32) * 3

        vad._speech_buffer.append(c1)
        vad._speech_buffer.append(c2)
        vad._speech_buffer.append(c3)
        vad._confidence_history.extend([0.8, 0.8, 0.8])
        vad._speech_samples = 480
        vad._is_speaking = True

        # Trim front 200 samples (c1 completely, and 40 of c2)
        vad.trim_front(200)
        self.assertEqual(vad._speech_samples, 280)
        self.assertEqual(len(vad._speech_buffer), 2)
        self.assertEqual(len(vad._speech_buffer[0]), 120)
        self.assertEqual(len(vad._speech_buffer[1]), 160)

    def test_local_qwen_context_history(self):
        translator = LocalQwenTranslator.__new__(LocalQwenTranslator)
        translator._model_name_or_path = "Qwen/Qwen3.5-4B"
        translator._target_language = "en"
        translator._system_prompt_template = "Translate {source_lang} to {target_lang}"
        translator._context_turns = 2
        translator._history = []

        translator._append_history("こんにちは", "Hello")
        self.assertEqual(len(translator._history), 1)
        self.assertEqual(translator._history[0], ("こんにちは", "Hello"))

        translator._append_history("元気ですか？", "How are you?")
        translator._append_history("散歩に行きます", "Going for a walk")
        # Should retain only the latest 2 turns when capped
        translator._append_history("天気配慮", "Weather care")
        self.assertLessEqual(len(translator._history), 4)

        translator.clear_history()
        self.assertEqual(len(translator._history), 0)

    def test_whisper_hallucination_detection(self):
        # Japanese outro/silence hallucinations
        self.assertTrue(text_segmenter.is_whisper_hallucination("ご視聴ありがとうございました"))
        self.assertTrue(text_segmenter.is_whisper_hallucination("ご視聴ありがとうございました！"))
        self.assertTrue(text_segmenter.is_whisper_hallucination("ご視聴いただき誠にありがとうございました"))
        self.assertTrue(text_segmenter.is_whisper_hallucination("最後までご視聴ありがとうございました"))
        self.assertTrue(text_segmenter.is_whisper_hallucination("チャンネル登録よろしくお願いします"))
        self.assertTrue(text_segmenter.is_whisper_hallucination("チャンネル登録よろしくお願いいたします"))

        # English outro/silence hallucinations
        self.assertTrue(text_segmenter.is_whisper_hallucination("Thank you for watching."))
        self.assertTrue(text_segmenter.is_whisper_hallucination("Thanks for watching!"))
        self.assertTrue(text_segmenter.is_whisper_hallucination("Thank you so much for watching"))
        self.assertTrue(text_segmenter.is_whisper_hallucination("Please like and subscribe"))
        self.assertTrue(text_segmenter.is_whisper_hallucination("Subtitles by the Amara.org community"))

        # Chinese outro/silence hallucinations
        self.assertTrue(text_segmenter.is_whisper_hallucination("谢谢观看"))
        self.assertTrue(text_segmenter.is_whisper_hallucination("感謝您的觀看"))

        # Legitimate conversational speech should NOT be filtered
        self.assertFalse(text_segmenter.is_whisper_hallucination("こんにちは、今日はいい天気ですね"))
        self.assertFalse(text_segmenter.is_whisper_hallucination("Thank you very much"))
        self.assertFalse(text_segmenter.is_whisper_hallucination("ありがとうございます"))
        self.assertFalse(text_segmenter.is_whisper_hallucination("I really like this place"))
        self.assertFalse(text_segmenter.is_whisper_hallucination(""))
        self.assertFalse(text_segmenter.is_whisper_hallucination("   "))


if __name__ == "__main__":
    unittest.main()

