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
