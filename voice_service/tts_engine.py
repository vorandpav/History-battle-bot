import os
import torch
from pathlib import Path
from TTS.api import TTS


class VoiceManager:
    def __init__(self, model_name="tts_models/multilingual/multi-dataset/xtts_v2"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[VoiceManager] Loading {model_name} on {self.device}")

        os.environ["COQUI_TOS_AGREED"] = "1"

        self.tts = TTS(model_name).to(self.device)

        base_dir = Path(__file__).resolve().parent

        self.speakers = {
            "stalin": base_dir / "speakers" / "stalin.wav",
            "churchill": base_dir / "speakers" / "churchill.wav",
        }

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

        return output_path