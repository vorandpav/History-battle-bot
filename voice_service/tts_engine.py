import os
from pathlib import Path

# Кэш моделей — только до import torch / TTS (иначе Coqui берёт %LocalAppData%).
_root = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv

    load_dotenv(_root / ".env")
except ImportError:
    pass
_cache = _root / ".cache"
os.environ.setdefault("TTS_HOME", str(_cache / "tts"))
os.environ.setdefault("HF_HUB_CACHE", str(_cache / "huggingface" / "hub"))
os.environ.setdefault("COQUI_TOS_AGREED", "1")

import torch
from TTS.api import TTS


def _speed_up_wav_inplace(path: str, rate: float) -> None:
    """Укорочение дорожки в `rate` раз при ~сохранении тона (librosa phase vocoder)."""
    if rate <= 1.0 + 1e-6:
        return
    import numpy as np
    import librosa
    import soundfile as sf

    data, sr = sf.read(path, always_2d=True)
    data = np.asarray(data, dtype=np.float32)
    peak = float(np.max(np.abs(data))) if data.size else 0.0
    if peak > 1.5:
        data = data / 32768.0
    channels = [librosa.effects.time_stretch(data[:, i], rate=rate) for i in range(data.shape[1])]
    min_len = min(len(c) for c in channels)
    out = np.stack([c[:min_len] for c in channels], axis=1)
    sf.write(path, np.clip(out, -1.0, 1.0), sr)


class VoiceManager:
    def __init__(self, model_name="tts_models/multilingual/multi-dataset/xtts_v2"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[VoiceManager] Кэш TTS: {os.environ.get('TTS_HOME')}")
        print(f"[VoiceManager] Loading {model_name} on {self.device}")

        self.tts = TTS(model_name).to(self.device)

        base_dir = Path(__file__).resolve().parent

        self.speakers = {
            "stalin": base_dir / "speakers" / "stalin.wav",
            "churchill": base_dir / "speakers" / "churchill.wav",
        }
        raw = os.getenv("VOICE_TIME_STRETCH_RATE", "1.4").strip().replace(",", ".")
        try:
            self._time_stretch_rate = float(raw)
        except ValueError:
            self._time_stretch_rate = 1.4
        if self._time_stretch_rate < 1.0:
            self._time_stretch_rate = 1.0
        print(f"[VoiceManager] Ускорение аудио после синтеза: x{self._time_stretch_rate:.3g}")

    def generate_voice(self, text: str, speaker_key: str, output_path: str):
        if speaker_key not in self.speakers:
            raise ValueError(f"Персонаж '{speaker_key}' не найден")

        ref_path = self.speakers[speaker_key]

        if not ref_path.exists():
            raise FileNotFoundError(f"Файл не найден: {ref_path}")

        self.tts.tts_to_file(
            text=text,
            file_path=output_path,
            speaker_wav=str(ref_path),
            language="ru",
            split_sentences=True
        )

        _speed_up_wav_inplace(output_path, self._time_stretch_rate)

        return output_path