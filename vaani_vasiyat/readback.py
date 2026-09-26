import base64
import hashlib
from pathlib import Path
from typing import Optional
from sarvamai import SarvamAI
from .bilingual_legal import BilingualDeed


def generate_audio_readback(
    client: SarvamAI,
    deed: BilingualDeed,
    output_audio_path: Path,
    speaker: str = "aditya",
) -> Path:
    """Generate audio readback of the drafted will using Bulbul v3 TTS."""
    # Synthesize the opening declaration and key bequest summary for the testator
    lines = deed.indic_draft.split("\n\n")
    # Take first 2-3 substantive paragraphs for auditory verification
    readback_text = " वसीयत का वाचन: " + " ".join(lines[:3])

    # Truncate if exceptionally long for a single TTS chunk (Bulbul limit)
    if len(readback_text) > 450:
        readback_text = readback_text[:450] + "..."

    response = client.text_to_speech.convert(
        text=readback_text,
        language_code=deed.target_language,
        speaker=speaker,
        model="bulbul:v3",
        output_audio_codec="wav",
        pace=0.95,  # Slightly deliberate pacing for elderly comprehension
    )

    if not response.audios or len(response.audios) == 0:
        raise RuntimeError("No audio received from Bulbul v3 TTS.")

    audio_bytes = base64.b64decode(response.audios[0])
    output_audio_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_audio_path, "wb") as f:
        f.write(audio_bytes)

    return output_audio_path
