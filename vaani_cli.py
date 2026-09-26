import argparse
import sys
from pathlib import Path

from vaani_vasiyat.orchestrator import run_vaani_vasiyat_pipeline
from vaani_vasiyat.merkle_anchor import WitnessRecord


def main():
    parser = argparse.ArgumentParser(
        description="Vaani Vasiyat (Voice Testament) — Sarvam AI Multimodal Indic Testamentary System"
    )
    parser.add_argument(
        "--audio",
        "-a",
        type=str,
        help="Path to testator audio narration file (.wav, .mp3).",
    )
    parser.add_argument(
        "--target-lang",
        "-l",
        type=str,
        default="hi-IN",
        help="Target language code for the bilingual deed (e.g. hi-IN, ta-IN, te-IN, bn-IN). Default: hi-IN",
    )
    parser.add_argument(
        "--clarifications",
        "-c",
        type=str,
        help="Clarifications to resolve legal ambiguities (e.g. 'Land is self-acquired, executor is Hariram').",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the complete pipeline on the pre-generated sample Hindi rural testator audio.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="vaani_output",
        help="Directory to store the printable legal deed, audio readback, and Merkle package.",
    )

    args = parser.parse_args()

    if args.demo:
        audio_file = Path("sample_testator_speech.wav")
        if not audio_file.exists():
            print("Error: sample_testator_speech.wav not found.")
            sys.exit(1)
    elif args.audio:
        audio_file = Path(args.audio)
        if not audio_file.exists():
            print(f"Error: File not found: {audio_file}")
            sys.exit(1)
    else:
        print("Please provide --audio <path> or use --demo to run with a synthesized testator.")
        parser.print_help()
        sys.exit(1)

    # Execute full multi-engine pipeline
    results = run_vaani_vasiyat_pipeline(
        audio_path=audio_file,
        target_language=args.target_lang,
        clarifications=args.clarifications,
        output_dir=Path(args.output_dir),
    )

    print("\n" + "=" * 65)
    print("PIPELINE EXECUTION SUMMARY")
    print("=" * 65)
    print(f"Testator:      {results['plan'].testator_name} ({results['plan'].residence})")
    print(f"Bequests:      {len(results['plan'].bequests)} clauses structured")
    print(f"Merkle Root:   {results['merkle_package'].merkle_root}")
    print(f"Printable Deed:{results['export_files']['html_deed']}")
    print(f"JSON Manifest: {results['export_files']['manifest']}")
    if results['readback_audio']:
        print(f"Audio Readback:{results['readback_audio']}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
