from __future__ import annotations

import io
import json
import subprocess
import wave
from pathlib import Path

import numpy as np
import soundfile as sf

from app.voice_module.noise import spectral_gate_placeholder

try:
    from vosk import KaldiRecognizer, Model
except Exception:  # pragma: no cover - optional dependency
    KaldiRecognizer = None
    Model = None


class SpeechToText:
    def __init__(
        self,
        engine: str,
        whisper_bin: str | None = None,
        whisper_model: str | None = None,
        vosk_model: str | None = None,
    ) -> None:
        self.engine = engine
        self.whisper_bin = whisper_bin
        self.whisper_model = whisper_model
        self.vosk_model = vosk_model

    def transcribe(self, audio_path: Path) -> tuple[str, str, float | None]:
        normalized_path = self._normalize_audio(audio_path)
        if self.engine == "whisper.cpp":
            return self._transcribe_whisper_cpp(normalized_path)
        if self.engine == "vosk":
            return self._transcribe_vosk(normalized_path)
        return ("Voice pipeline is in mock mode.", "en", None)

    def _normalize_audio(self, audio_path: Path) -> Path:
        samples, sample_rate = sf.read(str(audio_path), always_2d=False)
        if isinstance(samples, tuple):
            samples = samples[0]
        samples_array = np.asarray(samples, dtype=np.float32)
        if samples_array.ndim > 1:
            samples_array = samples_array.mean(axis=1)
        cleaned = spectral_gate_placeholder(samples_array)
        output_path = audio_path.with_suffix(".normalized.wav")
        sf.write(str(output_path), cleaned, sample_rate, subtype="PCM_16")
        return output_path

    def _transcribe_whisper_cpp(self, audio_path: Path) -> tuple[str, str, float | None]:
        if not self.whisper_bin or not self.whisper_model:
            raise RuntimeError("WHISPER_CPP_BIN and WHISPER_MODEL_PATH are required.")
        result = subprocess.run(
            [self.whisper_bin, "-m", self.whisper_model, "-f", str(audio_path), "-otxt", "-of", "-"],
            check=True,
            capture_output=True,
            text=True,
        )
        return (result.stdout.strip(), "auto", None)

    def _transcribe_vosk(self, audio_path: Path) -> tuple[str, str, float | None]:
        if Model is None or KaldiRecognizer is None:
            raise RuntimeError("vosk is not installed. Add vosk to the backend environment.")
        if not self.vosk_model:
            raise RuntimeError("VOSK_MODEL_PATH is required when STT_ENGINE=vosk.")
        model = Model(self.vosk_model)
        with wave.open(str(audio_path), "rb") as wav_file:
            recognizer = KaldiRecognizer(model, wav_file.getframerate())
            recognizer.SetWords(True)
            while True:
                data = wav_file.readframes(4000)
                if not data:
                    break
                recognizer.AcceptWaveform(data)
            result = json.loads(recognizer.FinalResult())
        transcript = result.get("text", "").strip()
        confidence = None
        if result.get("result"):
            scores = [item.get("conf", 0.0) for item in result["result"]]
            confidence = sum(scores) / len(scores)
        return (transcript, "auto", confidence)
