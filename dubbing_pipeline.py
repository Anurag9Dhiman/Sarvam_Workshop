import argparse
import base64
import os
import sys
import time
from pathlib import Path
from typing import List, Optional
import httpx
import pydantic
from sarvamai import SarvamAI

# Patch Sarvam SDK DubbingStartData to handle backend returning 'project_id' and 'task_submitted'
try:
    from sarvamai.types import dubbing_start_data
    class PatchedDubbingStartData(pydantic.BaseModel):
        job_id: Optional[str] = None
        project_id: Optional[str] = None
        status: Optional[str] = "processing"
        task_submitted: Optional[bool] = None
        task_id: Optional[str] = None
        model_config = pydantic.ConfigDict(extra="allow")
    dubbing_start_data.DubbingStartData = PatchedDubbingStartData
except Exception:
    pass

# Load .env if present and not already in environment
env_file = Path(__file__).resolve().parent / ".env"
if env_file.exists():
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("\"'")
                if k and not os.environ.get(k):
                    os.environ[k] = v


def get_client() -> SarvamAI:
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        print("Error: SARVAM_API_KEY environment variable is missing.")
        sys.exit(1)
    return SarvamAI(api_subscription_key=api_key)


def generate_sample_audio(client: SarvamAI, output_path: Path) -> Path:
    """Generate a clean English speech sample using Sarvam Bulbul TTS."""
    print("Generating demo audio sample with Sarvam TTS (Bulbul)...")
    text = (
        "Welcome to today's presentation. In this video, we explore how artificial "
        "intelligence and deep neural networks are transforming communication across India."
    )
    response = client.text_to_speech.convert(
        text=text,
        language_code="en-IN",
        speaker="aditya",
        model="bulbul:v3",
        output_audio_codec="wav",
    )
    if not response.audios or len(response.audios) == 0:
        raise RuntimeError("No audio returned from Text-to-Speech API.")

    audio_bytes = base64.b64decode(response.audios[0])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    print(f"Sample audio saved to: {output_path}")
    return output_path


def download_job_exports(
    client: SarvamAI, job_id: str, output_dir: Path, base_stem: str, max_wait_secs: int = 60
):
    """Wait for export files to be packaged and download them locally."""
    print("\nPreparing export downloads...")
    start_time = time.time()
    exports = []
    while time.time() - start_time < max_wait_secs:
        export_res = client.dubbing.get_export_status(job_id=job_id)
        if export_res.data.exports and len(export_res.data.exports) > 0:
            exports = export_res.data.exports
            break
        print("  -> Waiting for export files to be packaged and signed...")
        time.sleep(4)

    output_dir.mkdir(parents=True, exist_ok=True)
    if not exports:
        print("No export files available yet. You can resume later with:")
        print(f"  python3 dubbing_pipeline.py --resume {job_id}")
        return

    print(f"Found {len(exports)} export file(s):")
    for exp in exports:
        exp_type = exp.export_type  # 'video', 'audio', 'srt'
        lang = exp.target_language
        dl_url = exp.download_url
        filename = f"{base_stem}_{lang}_{exp_type}"
        if exp_type == "video":
            filename += ".mp4"
        elif exp_type == "audio":
            filename += ".wav"
        elif exp_type == "srt":
            filename += ".srt"
        else:
            filename += ".bin"

        dest_file = output_dir / filename
        print(f"  - [{exp_type.upper()}] ({lang}) -> Downloading to {dest_file.name}...")

        # Download with streaming
        with httpx.stream("GET", dl_url, timeout=120.0) as r:
            r.raise_for_status()
            with open(dest_file, "wb") as out_f:
                for chunk in r.iter_bytes(chunk_size=8192):
                    out_f.write(chunk)
        print(f"    Saved: {dest_file} ({dest_file.stat().st_size} bytes)")

    print(f"\nAll dubbing artifacts saved in: {output_dir.resolve()}")


def monitor_job(client: SarvamAI, job_id: str):
    """Poll job status until completion or failure."""
    print(f"\nMonitoring job progress (Job ID: {job_id})...")
    last_step = ""
    while True:
        status_res = client.dubbing.get_live_status(job_id=job_id)
        data = status_res.data
        status = (data.status or "").lower()
        progress = data.progress or 0
        step_label = data.current_step_label or data.current_step or "processing"

        if step_label != last_step or progress % 20 == 0:
            print(f"  -> Progress: {progress:3d}% | Status: {status:10s} | Step: {step_label}")
            last_step = step_label

        if status in ["completed", "success"]:
            print(f"\nDubbing completed successfully! (Progress: 100%)")
            break
        elif status in ["failed", "error"]:
            err_msg = data.error_message or "Unknown error occurred"
            print(f"\nDubbing failed: {err_msg}")
            sys.exit(1)

        time.sleep(5)


def run_dubbing_job(
    client: SarvamAI,
    file_path: Path,
    source_lang: str = "en-IN",
    target_langs: Optional[List[str]] = None,
    register: str = "common-indic",
    pace_preset: str = "normal",
    voice_cloning: bool = True,
    output_dir: Path = Path("dubbed_outputs"),
):
    if target_langs is None:
        target_langs = ["hi-IN"]

    print("\n" + "=" * 60)
    print("SARVAM VIDEO & AUDIO DUBBING PIPELINE")
    print("=" * 60)
    print(f"File to dub:       {file_path} ({file_path.stat().st_size} bytes)")
    print(f"Source Language:   {source_lang}")
    print(f"Target Languages:  {', '.join(target_langs)}")
    print(f"Tone (Register):   {register}")
    print(f"Pace Preset:       {pace_preset}")
    print(f"Voice Cloning:     {voice_cloning}")
    print(f"Output Directory:  {output_dir}")
    print("=" * 60 + "\n")

    # Step 1: Create Job
    print("[1/4] Creating dubbing job with Sarvam AI...")
    job_name = f"dubbing_{file_path.stem[:20]}_{int(time.time())}"
    job_response = client.dubbing.create(
        source_language_code=source_lang,
        target_language_codes=target_langs,
        export_options=["video", "audio", "srt"],
        voice_cloning=voice_cloning,
        register=register,
        pace_preset=pace_preset,
        job_name=job_name,
    )

    job_data = job_response.data
    job_id = job_data.job_id
    upload_url = job_data.upload_url
    print(f"Job created successfully! Job ID: {job_id}")

    # Step 2: Upload File
    print(f"[2/4] Uploading {file_path.name} to Sarvam storage...")
    client.dubbing.upload(upload_url=upload_url, file=file_path)
    print("Upload completed.")

    # Step 3: Start Job
    print(f"[3/4] Triggering dubbing pipeline for Job ID: {job_id}...")
    try:
        client.dubbing.start(job_id=job_id)
    except Exception as e:
        # Gracefully handle SDK deserialization bug when backend responds with project_id
        if "ValidationError" in type(e).__name__ or "DubbingStartResponse" in str(e):
            pass
        else:
            raise
    print("Dubbing pipeline started.")

    # Step 4: Poll Status
    print("\n[4/4] Monitoring job progress...")
    monitor_job(client, job_id)

    # Step 5: Download Exports
    download_job_exports(client, job_id, output_dir, file_path.stem)


def main():
    parser = argparse.ArgumentParser(
        description="Sarvam AI Video/Audio Dubbing Pipeline with Tone Control and Voice Cloning"
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        help="Path to the video (.mp4, .mov) or audio (.wav, .mp3) file to dub.",
    )
    parser.add_argument(
        "--source-lang",
        type=str,
        default="en-IN",
        help="Source language code (e.g. en-IN, hi-IN). Default: en-IN",
    )
    parser.add_argument(
        "--target-lang",
        type=str,
        default="hi-IN",
        help="Target language code (e.g. hi-IN, ta-IN, te-IN, bn-IN, mr-IN). Default: hi-IN",
    )
    parser.add_argument(
        "--register",
        type=str,
        default="common-indic",
        choices=["formal", "common-indic", "modern-colloquial", "classic-colloquial", "academic", "auto"],
        help="Tone register for translation. Default: common-indic",
    )
    parser.add_argument(
        "--pace",
        type=str,
        default="normal",
        choices=["slow", "moderate", "normal", "fast"],
        help="Pace preset for speech synthesis. Default: normal",
    )
    parser.add_argument(
        "--no-voice-cloning",
        action="store_true",
        help="Disable voice cloning (uses standard synthetic voices instead of speaker voice).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="dubbed_outputs",
        help="Directory to save downloaded dubbed video/audio/srt files.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Synthesize a sample English audio clip using Sarvam TTS and dub it into the target language.",
    )
    parser.add_argument(
        "--resume",
        type=str,
        help="Resume/download exports for an existing Job ID directly.",
    )

    args = parser.parse_args()
    client = get_client()

    if args.resume:
        monitor_job(client, args.resume)
        download_job_exports(client, args.resume, Path(args.output_dir), f"job_{args.resume[:8]}")
        return

    if args.demo:
        demo_audio_file = Path("demo_source_speech.wav")
        if not demo_audio_file.exists():
            generate_sample_audio(client, demo_audio_file)
        target_file = demo_audio_file
    elif args.file:
        target_file = Path(args.file)
        if not target_file.exists():
            print(f"Error: File not found: {target_file}")
            sys.exit(1)
    else:
        print("Please provide a media file using --file <path>, or use --demo, or use --resume <job_id>.")
        parser.print_help()
        sys.exit(1)

    run_dubbing_job(
        client=client,
        file_path=target_file,
        source_lang=args.source_lang,
        target_langs=[args.target_lang],
        register=args.register,
        pace_preset=args.pace,
        voice_cloning=not args.no_voice_cloning,
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    main()
