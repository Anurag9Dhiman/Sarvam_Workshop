import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel
from sarvamai import SarvamAI


class AudioIntakeResult(BaseModel):
    file_path: str
    audio_sha256: str
    transcript: str
    language_code: str
    words_count: int
    timestamps_available: bool


def hash_file(file_path: Path) -> str:
    """Compute SHA-256 hash of a file for tamper-evident provenance."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def process_audio_intake(
    client: SarvamAI,
    audio_path: Path,
    language_code: str = "hi-IN",
    with_timestamps: bool = True,
) -> AudioIntakeResult:
    """Transcribe spoken testator testimony using Sarvam Saaras v3 ASR."""
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    audio_hash = hash_file(audio_path)

    with open(audio_path, "rb") as f:
        res = client.speech_to_text.transcribe(
            file=f,
            model="saaras:v3",
            language_code=language_code,
            with_timestamps=with_timestamps,
        )

    words_count = 0
    if res.timestamps and res.timestamps.words:
        words_count = len(res.timestamps.words)

    return AudioIntakeResult(
        file_path=str(audio_path),
        audio_sha256=audio_hash,
        transcript=res.transcript or "",
        language_code=res.language_code or language_code,
        words_count=words_count,
        timestamps_available=words_count > 0,
    )
