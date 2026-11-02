import unittest
from PyQt6.QtWidgets import QApplication
import model_manager
import control_panel
import main as main_module


class TestASREngineOptions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_model_ids_and_display_names(self):
        self.assertEqual(
            model_manager.ASR_MODEL_IDS["kotoba-whisper"],
            "kotoba-tech/kotoba-whisper-v2.0-faster",
        )
        self.assertEqual(
            model_manager.ASR_MODEL_IDS["whisper-turbo"],
            "deepdml/faster-whisper-large-v3-turbo-ct2",
        )
        self.assertEqual(
            model_manager.ASR_MODEL_IDS["anime-whisper"],
            "kotoba-tech/kotoba-whisper-v2.0-faster",
        )
        self.assertEqual(
            model_manager.ASR_DISPLAY_NAMES["kotoba-whisper"],
            "Kotoba-Whisper v2.0",
        )
        self.assertEqual(
            model_manager.ASR_DISPLAY_NAMES["whisper-turbo"],
            "Whisper Large-v3 Turbo",
        )
        self.assertEqual(
            model_manager.ASR_DISPLAY_NAMES["sensevoice"],
            "SenseVoice Small",
        )
        self.assertIn("large-v3-turbo", model_manager._WHISPER_SIZES)

    def test_control_panel_engine_selection(self):
        cfg = main_module.load_config()

        # Test index mapping for kotoba-whisper
        panel = control_panel.ControlPanel(cfg, saved_settings={"asr_engine": "kotoba-whisper"})
        self.addCleanup(panel.close)
        self.assertEqual(panel._asr_engine.currentIndex(), 0)
        self.assertEqual(panel.get_settings()["asr_engine"], "kotoba-whisper")

        # Test legacy anime-whisper maps to index 0
        panel_legacy = control_panel.ControlPanel(cfg, saved_settings={"asr_engine": "anime-whisper"})
        self.addCleanup(panel_legacy.close)
        self.assertEqual(panel_legacy._asr_engine.currentIndex(), 0)
        self.assertEqual(panel_legacy.get_settings()["asr_engine"], "kotoba-whisper")

        # Test whisper-turbo selection
        panel._asr_engine.setCurrentIndex(1)
        panel._apply_settings()
        self.assertEqual(panel.get_settings()["asr_engine"], "whisper-turbo")

        # Test sensevoice selection
        panel._asr_engine.setCurrentIndex(2)
        panel._apply_settings()
        self.assertEqual(panel.get_settings()["asr_engine"], "sensevoice")

        # Test standard whisper selection
        panel._asr_engine.setCurrentIndex(3)
        panel._apply_settings()
        self.assertEqual(panel.get_settings()["asr_engine"], "whisper")

        # Test remote-whisper selection
        panel._asr_engine.setCurrentIndex(4)
        panel._apply_settings()
        self.assertEqual(panel.get_settings()["asr_engine"], "remote-whisper")
