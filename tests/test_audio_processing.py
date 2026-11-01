import unittest
import numpy as np

from audio_capture import AudioCapture
from vad_processor import VADProcessor


class TestAudioProcessing(unittest.TestCase):
    def test_stereo_downmix_equivalence(self):
        rng = np.random.default_rng(42)
        stereo = rng.standard_normal(4096).astype(np.float32)

        # Baseline: matrix reshape and reduction
        expected = stereo.reshape(-1, 2).mean(axis=1)

        # Fast path: sliced vector addition
        ac = AudioCapture()
        actual = ac._resample_to_mono(stereo.tobytes(), native_channels=2, native_rate=16000)

        np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-6)

    def test_resample_caching_consistency(self):
        ac = AudioCapture(sample_rate=16000)
        rng = np.random.default_rng(42)
        audio = rng.standard_normal(4410).astype(np.float32)  # 44.1kHz 100ms chunk

        # First call (populates cache)
        out1 = ac._resample_to_mono(audio.tobytes(), native_channels=1, native_rate=44100)
        self.assertIn((len(audio), 44100, 16000), ac._resample_cache)

        # Second call (uses cached indices)
        out2 = ac._resample_to_mono(audio.tobytes(), native_channels=1, native_rate=44100)

        np.testing.assert_array_equal(out1, out2)

    def test_vad_energy_rms_accuracy(self):
        vad = VADProcessor(sample_rate=16000)
        vad.mode = "energy"
        rng = np.random.default_rng(42)
        chunk = rng.standard_normal(512).astype(np.float32)

        expected_rms = float(np.sqrt(np.mean(chunk**2)))
        expected_conf = min(1.0, expected_rms / (vad.energy_threshold * 2))

        actual_conf = vad._energy_confidence(chunk)
        self.assertAlmostEqual(actual_conf, expected_conf, places=6)


if __name__ == "__main__":
    unittest.main()
