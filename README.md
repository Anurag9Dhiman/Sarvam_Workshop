# Sarvam AI Indic Video/Audio Dubbing & Conversational Suite

Production-ready implementation for Sarvam AI's Indic models:
1. **Conversational AI (`sarvam-105b-conversations`)**: Conversational reasoning and dialogue model tuned for Indian languages.
2. **Video & Audio Dubbing Pipeline (`client.dubbing`)**: Full-pipeline audio/video dubbing with cross-lingual voice cloning and tone control (`register`).

---

## Setup

1. **Clone the repository and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key:**
   Copy `.env.example` to `.env` and add your Sarvam API subscription key:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```env
   SARVAM_API_KEY=your_actual_key_here
   ```

---

## 1. Chat Completion (`sarvam-105b-conversations`)

Test conversational reasoning:
```bash
python3 main.py
```

---

## 2. Video & Audio Dubbing Pipeline

Translate, re-voice, and time-sync any video or audio file with speaker voice cloning and tone control across 12+ Indic languages.

### Tone Registers (`--register`):
- `formal`: Corporate, polite, and institutional phrasing.
- `common-indic`: Natural, everyday conversational Indian phrasing.
- `modern-colloquial`: Contemporary, urban phrasing.
- `classic-colloquial`: Traditional idioms and regional expressions.
- `academic`: Exact technical / textbook terms.
- `auto`: Automatically matches the tone of the source audio.

### Dub an existing file:
```bash
python3 dubbing_pipeline.py \
  --file /path/to/video.mp4 \
  --source-lang en-IN \
  --target-lang hi-IN \
  --register formal \
  --pace normal
```

### Run self-contained demo:
```bash
python3 dubbing_pipeline.py --demo --target-lang hi-IN --register common-indic
```

### Resume/download exports for an existing job:
```bash
python3 dubbing_pipeline.py --resume <job_id>
```

Outputs are automatically saved into `./dubbed_outputs/`:
- `.mp4` (dubbed video)
- `.wav` (mastered dubbed audio track)
- `.srt` (synchronized subtitles in target language)

---

## 3. Multi-Engine Test Suite (`sarvam_suite.py`)

Run live smoke tests across all 5 core Sarvam engines:
```bash
python3 sarvam_suite.py --test-all
```

Or invoke individual tools directly:
- **Speech-to-Text (`Saaras v3`)**:
  ```bash
  python3 sarvam_suite.py --stt dubbed_outputs/job_fda3b857_hi-IN_audio.wav
  ```
- **Translation & Hinglish Code-Mixing (`Mayura`)**:
  ```bash
  python3 sarvam_suite.py --translate "Please submit your land registration papers by tomorrow."
  ```
- **Direct Voice Cloning (`POST /voices/clone`)**:
  ```bash
  python3 sarvam_suite.py --clone demo_source_speech.wav
  ```
---

## 4. Vaani Vasiyat (Voice Testament) Pipeline

The full multimodal Indic testamentary intake and drafting system pitched in the workshop:
1. **Saaras v3 (ASR)**: Dialectal speech transcription and SHA-256 voice hashing.
2. **Sarvam-105B (Paralegal Audit)**: Structuring informal narration into testamentary clauses while actively auditing for:
   - Ambiguous boundary descriptions (khasra/survey numbers).
   - Hindu coparcenary / ancestral vs. self-acquired land risks.
   - Missing executors or omitted residuary estates.
3. **Mayura (Translation)**: Compiles statutory bilingual legal will (Section 63 of Indian Succession Act, 1925).
4. **Bulbul v3 (Audio Readback)**: Synthesizes high-fidelity speech reading back the drafted clauses to illiterate/elderly testators for verbal verification.
5. **Cryptographic Merkle Anchor**: Computes Merkle Root across Audio Recording, Saaras Transcript, Witness Attestations, and Legal Deed for Section 63 BSA / 65B IEA electronic admissibility.

### Run the complete demo:
```bash
python3 vaani_cli.py --demo
```

### Run on your own voice recording:
```bash
python3 vaani_cli.py \
  --audio /path/to/testator_recording.wav \
  --target-lang hi-IN \
  --clarifications "The Rampur land is self-acquired. Hariram is the executor."
```

Generated deliverables are saved to `./vaani_output/`:
- `*_testament.html` (Printable bilingual legal deed with thumb impression and witness signature boxes)
- `*_manifest.json` (Cryptographic Merkle tree package with leaf hashes)
- `*_readback.wav` (Native audio confirmation track)


