from __future__ import annotations

import json
import platform
import subprocess
import wave
from pathlib import Path

import numpy as np
import soundfile as sf

from app.voice_module.command_normalizer import normalize_spoken_command
from app.voice_module.noise import spectral_gate_placeholder

try:
    from vosk import KaldiRecognizer, Model
except Exception:  # pragma: no cover - optional dependency
    KaldiRecognizer = None
    Model = None


LANGUAGE_TO_LOCALES = {
    "auto": ["en-US", "hi-IN", "te-IN"],
    "en": ["en-US"],
    "hi": ["hi-IN", "en-US"],
    "te": ["te-IN", "en-US"],
}


class SpeechToText:
    def __init__(
        self,
        engine: str,
        whisper_bin: str | None = None,
        whisper_model: str | None = None,
        vosk_model: str | None = None,
    ) -> None:
        self.whisper_bin = whisper_bin
        self.whisper_model = whisper_model
        self.vosk_model = vosk_model
        self.engine = self._resolve_engine(engine)

    def transcribe(self, audio_path: Path, requested_language: str = "auto") -> tuple[str, str, float | None]:
        normalized_path = self._normalize_audio(audio_path)
        if self.engine == "whisper.cpp":
            transcript, detected_language, confidence = self._transcribe_whisper_cpp(normalized_path)
            return normalize_spoken_command(transcript), detected_language, confidence
        if self.engine == "vosk":
            transcript, detected_language, confidence = self._transcribe_vosk(normalized_path)
            return normalize_spoken_command(transcript), detected_language, confidence
        if self.engine == "macos-speech":
            transcript, detected_language, confidence = self._transcribe_macos_speech(normalized_path, requested_language)
            return normalize_spoken_command(transcript), detected_language, confidence
        return (
            "Voice recognition is not configured on this machine. Configure Vosk or Whisper.cpp for fully offline voice commands.",
            requested_language if requested_language != "auto" else "en",
            None,
        )

    def _resolve_engine(self, engine: str) -> str:
        normalized = engine.lower().strip()
        if normalized not in {"", "mock", "auto"}:
            return normalized
        if self.vosk_model and Path(self.vosk_model).exists() and Model is not None:
            return "vosk"
        if self.whisper_bin and self.whisper_model and Path(self.whisper_model).exists():
            return "whisper.cpp"
        if platform.system().lower() == "darwin":
            return "macos-speech"
        return "mock"

    def _normalize_audio(self, audio_path: Path) -> Path:
        samples, sample_rate = sf.read(str(audio_path), always_2d=False)
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

    def _transcribe_macos_speech(self, audio_path: Path, requested_language: str) -> tuple[str, str, float | None]:
        script_path = Path(__file__).with_name("macos_stt.swift")
        locales = ",".join(LANGUAGE_TO_LOCALES.get(requested_language, LANGUAGE_TO_LOCALES["auto"]))
        result = subprocess.run(
            ["xcrun", "swift", str(script_path), str(audio_path), locales],
            check=False,
            capture_output=True,
            text=True,
        )
        stdout = result.stdout.strip() or "{}"
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(result.stderr.strip() or f"Unable to decode macOS speech output: {exc}") from exc
        if result.returncode != 0:
            raise RuntimeError(payload.get("error") or result.stderr.strip() or "macOS speech transcription failed.")
        transcript = (payload.get("transcript") or "").strip()
        if not transcript:
            raise RuntimeError(payload.get("error") or "No speech detected from the recorded audio.")
        return transcript, payload.get("detected_language", requested_language), None
