import unittest
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from subtitle_overlay import SubtitleOverlay, DragHandle
from subtitle_window import SubtitleWindow
import main


class TestOverlayOptions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_drag_handle_has_no_taskbar_check(self):
        handle = DragHandle()
        self.assertFalse(hasattr(handle, "_taskbar_check"))
        self.assertFalse(hasattr(handle, "taskbar_toggled"))
        self.assertTrue(hasattr(handle, "_ct_check"))
        self.assertTrue(hasattr(handle, "_topmost_check"))
        self.assertTrue(hasattr(handle, "_auto_scroll"))

    def test_overlay_flags_have_no_tool(self):
        cfg = {
            "font_family": "Segoe UI",
            "font_size": 20,
            "font_color": "#ffffff",
            "outline_color": "#000000",
            "outline_width": 2,
            "opacity": 0.9,
        }
        overlay = SubtitleOverlay(cfg)
        self.assertFalse(hasattr(overlay, "_set_taskbar"))
        flags = overlay.windowFlags()
        self.assertNotEqual(flags & Qt.WindowType.WindowType_Mask, Qt.WindowType.Tool)
        self.assertEqual(flags & Qt.WindowType.WindowType_Mask, Qt.WindowType.Window)
        self.assertTrue(bool(flags & Qt.WindowType.FramelessWindowHint))
        self.assertTrue(bool(flags & Qt.WindowType.WindowStaysOnTopHint))

    def test_restore_options(self):
        cfg = {
            "font_family": "Segoe UI",
            "font_size": 20,
            "font_color": "#ffffff",
            "outline_color": "#000000",
            "outline_width": 2,
            "opacity": 0.9,
        }
        overlay = SubtitleOverlay(cfg)
        overlay.restore_options(click_through=True, topmost=False, auto_scroll=False)

        self.assertTrue(overlay._handle._ct_check.isChecked())
        self.assertTrue(overlay._click_through)
        self.assertFalse(overlay._handle._topmost_check.isChecked())
        self.assertFalse(bool(overlay.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))
        self.assertFalse(overlay._handle._auto_scroll.isChecked())
        self.assertFalse(overlay._handle.auto_scroll)

        overlay.restore_options(click_through=False, topmost=True, auto_scroll=True)
        self.assertFalse(overlay._handle._ct_check.isChecked())
        self.assertFalse(overlay._click_through)
        self.assertTrue(overlay._handle._topmost_check.isChecked())
        self.assertTrue(bool(overlay.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))
        self.assertTrue(overlay._handle._auto_scroll.isChecked())
        self.assertTrue(overlay._handle.auto_scroll)

    def test_toggling_topmost_keeps_overlay_visible(self):
        cfg = {
            "font_family": "Segoe UI",
            "font_size": 20,
            "font_color": "#ffffff",
            "outline_color": "#000000",
            "outline_width": 2,
            "opacity": 0.9,
        }
        overlay = SubtitleOverlay(cfg)
        overlay.show()
        self.assertTrue(overlay.isVisible())

        # Uncheck topmost
        overlay._handle._topmost_check.setChecked(False)
        self.app.processEvents()
        self.assertTrue(overlay.isVisible(), "Overlay must stay visible after unchecking topmost")
        self.assertFalse(bool(overlay.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))

        # Check topmost again
        overlay._handle._topmost_check.setChecked(True)
        self.app.processEvents()
        self.assertTrue(overlay.isVisible(), "Overlay must stay visible after re-checking topmost")
        self.assertTrue(bool(overlay.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))

    def test_subwin_position_restore_and_move(self):
        # Test restoring position near bottom of primary screen (e.g. under video)
        geo = self.app.primaryScreen().availableGeometry()
        target_x = geo.left() + 200
        target_y = geo.bottom() - 200
        subwin = SubtitleWindow({"window_x": target_x, "window_y": target_y})
        self.assertEqual(subwin.x(), target_x)
        self.assertEqual(subwin.y(), target_y)

        # Test moveEvent debounced save when visible
        subwin.show()
        new_x = target_x + 50
        new_y = target_y - 20
        subwin.move(new_x, new_y)
        self.assertEqual(subwin.x(), new_x)
        self.assertEqual(subwin.y(), new_y)
        self.assertTrue(hasattr(subwin, "_pos_save_timer"))
        self.assertTrue(subwin._pos_save_timer.isActive())
        subwin.close()

    def test_subwin_position_stays_fixed_during_text_updates(self):
        sub = SubtitleWindow({"window_x": 500, "window_y": 400})
        sub.show()
        self.assertEqual(sub.x(), 500)
        self.assertEqual(sub.y(), 400)
        sub.update_text("Hello", {"en": "Hello world"})
        self.assertEqual(sub.x(), 500)
        self.assertEqual(sub.y(), 400)
        sub.close()

    def test_icon_exists_and_loads(self):
        root = Path(__file__).resolve().parent.parent
        app_ico = root / "app.ico"
        icon_ico = root / "icon.ico"
        app_png = root / "app_icon.png"
        exe_file = root / "LiveTranslate.exe"

        self.assertTrue(app_ico.exists(), "app.ico missing")
        self.assertTrue(icon_ico.exists(), "icon.ico missing")
        self.assertTrue(app_png.exists(), "app_icon.png missing")
        self.assertTrue(exe_file.exists(), "LiveTranslate.exe missing")

        icon = main.create_app_icon()
        sizes = [s.width() for s in icon.availableSizes()]
        self.assertIn(256, sizes)
        self.assertIn(32, sizes)
        self.assertIn(16, sizes)

    def test_dynamic_memory_threshold(self):
        from unittest.mock import MagicMock
        from main import LiveTranslateApp

        cfg_qwen = {"translation": {"use_local_qwen": True, "target_language": "en", "max_tokens": 64, "temperature": 0.3}, "audio": {"sample_rate": 16000, "chunk_duration": 0.5}, "asr": {"vad_threshold": 0.1, "min_speech_duration": 0.4, "max_speech_duration": 8.0, "device": "cpu", "model_size": "medium"}}
        app_qwen = LiveTranslateApp.__new__(LiveTranslateApp)
        import psutil
        total_ram = psutil.virtual_memory().total / (1024 * 1024)
        expected = max(14336, int(total_ram * 0.85))
        app_qwen._mem_threshold_mb = expected
        self.assertGreaterEqual(app_qwen._mem_threshold_mb, 14336)
        # 5315 MB (as shown in user screenshot) should be well below the threshold
        self.assertLess(5315, app_qwen._mem_threshold_mb)


if __name__ == "__main__":
    unittest.main()
