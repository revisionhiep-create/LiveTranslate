import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import torch  # noqa: F401 - must precede PyQt6 on Windows
from PyQt6.QtWidgets import QApplication

import control_panel
import main as main_module
import translator as translator_module
from subtitle_overlay import SubtitleOverlay
from subtitle_window import DEFAULT_SUBTITLE_WIN_SETTINGS


class TargetLanguagePersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.settings_path = Path(self.tmpdir.name) / "user_settings.json"

        self.settings_patch = patch.object(
            control_panel, "SETTINGS_FILE", self.settings_path
        )
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)

        self.client_patch = patch.object(
            translator_module,
            "make_openai_client",
            side_effect=lambda *a, **kw: MagicMock(),
        )
        self.client_patch.start()
        self.addCleanup(self.client_patch.stop)

        self.audio_patch = patch.object(main_module, "AudioCapture")
        self.vad_patch = patch.object(main_module, "VADProcessor")
        self.transcript_patch = patch.object(main_module, "TranscriptWriter")
        self.audio_mock = self.audio_patch.start()
        self.vad_mock = self.vad_patch.start()
        self.transcript_mock = self.transcript_patch.start()
        self.addCleanup(self.audio_patch.stop)
        self.addCleanup(self.vad_patch.stop)
        self.addCleanup(self.transcript_patch.stop)
        self.audio_mock.return_value._device_name = None

    def test_defaults_are_english(self):
        cfg = main_module.load_config()
        self.assertEqual(cfg["translation"]["target_language"], "en")

        tl = translator_module.Translator("http://localhost:1234/v1", "k", "m")
        self.assertEqual(tl._target_language, "en")

        overlay = SubtitleOverlay({})
        self.addCleanup(overlay.close)
        self.assertEqual(overlay._handle._target_lang.currentData(), "en")

        panel = control_panel.ControlPanel(cfg, saved_settings=None)
        self.addCleanup(panel.close)
        self.assertEqual(panel.get_settings()["target_language"], "en")

        translation_lines = [
            line
            for line in DEFAULT_SUBTITLE_WIN_SETTINGS["lines"]
            if line.get("type") == "translation"
        ]
        self.assertTrue(all(line.get("lang") == "en" for line in translation_lines))

    def test_overlay_target_change_persists_across_control_panel_saves(self):
        cfg = main_module.load_config()
        initial_saved = {
            "target_language": "zh",
            "asr_language": "ja",
            "asr_engine": "anime-whisper",
        }
        panel = control_panel.ControlPanel(cfg, saved_settings=dict(initial_saved))
        self.addCleanup(panel.close)

        overlay = SubtitleOverlay({})
        self.addCleanup(overlay.close)
        overlay.set_target_language("zh")

        live_app = main_module.LiveTranslateApp(cfg)
        live_app.set_overlay(overlay)
        live_app.set_panel(panel)
        overlay.target_language_changed.connect(live_app._on_target_language_changed)

        # Avoid actually spawning an ASR worker when ControlPanel applies settings
        with patch.object(live_app, "_switch_asr_engine"):
            # Simulate user selecting English in the overlay Target dropdown
            en_idx = overlay._handle._target_lang.findData("en")
            self.assertGreaterEqual(en_idx, 0)
            overlay._handle._target_lang.setCurrentIndex(en_idx)

            self.assertEqual(live_app._target_language, "en")
            self.assertEqual(live_app._translator._target_language, "en")
            self.assertEqual(panel.get_settings()["target_language"], "en")

            # Simulate user changing another setting in ControlPanel (triggers auto-save)
            panel._timeout_spin.setValue(8)
            panel._do_auto_save()

            # Target language must remain English everywhere and on disk
            self.assertEqual(live_app._target_language, "en")
            self.assertEqual(live_app._translator._target_language, "en")
            self.assertEqual(overlay._handle._target_lang.currentData(), "en")
            self.assertEqual(panel.get_settings()["target_language"], "en")

            persisted = json.loads(self.settings_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["target_language"], "en")

    def test_english_punctuation_normalization(self):
        norm = translator_module.normalize_translation_text
        self.assertEqual(
            norm("Chup-chup... Hmm, so that\u2019s what you mean, right?", "en"),
            "Chup-chup... Hmm, so that's what you mean, right?",
        )
        self.assertEqual(
            norm("\u2026Hm? Hm. That\u2019s right. Then I\u2019ll check the report later.", "en"),
            "...Hm? Hm. That's right. Then I'll check the report later.",
        )
        self.assertEqual(
            norm("Yes, in that one, there\u2019s a part where it\u2019s not Su\u2019s Ren at all\u2026", "en"),
            "Yes, in that one, there's a part where it's not Su's Ren at all...",
        )
        self.assertEqual(
            norm("S\u016b\u2019s \u201cjuicy\u201d stuffed animals", "en"),
            'S\u016b\'s "juicy" stuffed animals',
        )
        # Literal spaced contractions are collapsed while valid possessives/quotes stay intact
        self.assertEqual(
            norm("Yes, I' ll check if that' s Su' s report and don' t worry.", "en"),
            "Yes, I'll check if that's Su's report and don't worry.",
        )
        self.assertEqual(
            norm("The boys' shoes and 'stop' right now.", "en"),
            "The boys' shoes and 'stop' right now.",
        )
        # CJK targets preserve full-width punctuation
        cjk = "\u201c\u592a\u5389\u5bb3\u4e86\u2026\u201d"
        self.assertEqual(norm(cjk, "zh"), cjk)
        self.assertEqual(norm(cjk, "ja"), cjk)

    def test_streaming_and_history_normalize_curly_apostrophes(self):
        tl = translator_module.Translator("http://localhost:1234/v1", "k", "m")
        tl.set_context_turns(5)

        chunk1 = MagicMock()
        chunk1.usage = None
        chunk1.choices = [MagicMock(delta=MagicMock(content="Then I\u2019"))]
        chunk2 = MagicMock()
        chunk2.usage = None
        chunk2.choices = [MagicMock(delta=MagicMock(content="ll check that\u2019s fine\u2026"))]
        tl._client.chat.completions.create.return_value = [chunk1, chunk2]

        partials = list(tl.translate_iter("\u3058\u3083\u3042\u306d", "ja"))
        self.assertEqual(
            partials,
            [
                "Then I'",
                "Then I'll check that's fine...",
                "Then I'll check that's fine...",
            ],
        )
        self.assertEqual(tl._history, [("\u3058\u3083\u3042\u306d", "Then I'll check that's fine...")])


if __name__ == "__main__":
    unittest.main()

