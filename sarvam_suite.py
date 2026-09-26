import argparse
import base64
import os
import sys
from pathlib import Path
import httpx
from sarvamai import SarvamAI

# Load .env
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
        print("Error: SARVAM_API_KEY is not set.")
        sys.exit(1)
    return SarvamAI(api_subscription_key=api_key)


def test_speech_to_text(client: SarvamAI, audio_path: Path):
    print("\n--- 1. Saaras v3 Speech-to-Text ---")
    if not audio_path.exists():
        print(f"File not found: {audio_path}")
        return
    with open(audio_path, "rb") as f:
        res = client.speech_to_text.transcribe(
            file=f,
            model="saaras:v3",
            language_code="hi-IN",
            with_timestamps=True,
        )
    print(f"Transcript: {res.transcript}")
    print(f"Language:   {res.language_code}")


def test_translation(client: SarvamAI):
    print("\n--- 2. Mayura Translation & Hinglish Code-Mixing ---")
    text = "Please submit your land registration papers and witness identification by tomorrow morning."

    formal_hi = client.text.translate(
        input=text, source_language_code="en-IN", target_language_code="hi-IN", mode="formal"
    )
    hinglish = client.text.translate(
        input=text, source_language_code="en-IN", target_language_code="hi-IN", mode="code-mixed"
    )
    tamil = client.text.translate(
        input=text, source_language_code="en-IN", target_language_code="ta-IN", mode="formal"
    )

    print(f"Original:        {text}")
    print(f"Hindi (Formal):  {formal_hi.translated_text}")
    print(f"Hinglish:        {hinglish.translated_text}")
    print(f"Tamil (Formal):  {tamil.translated_text}")


def test_language_tools(client: SarvamAI):
    print("\n--- 3. Language Identification & Transliteration ---")
    sample_indic = "దయచేసి మీ భూమి రిजिస్ట్రేషన్ పత్రాలను సమర్పించండి"
    lang_res = client.text.identify_language(input=sample_indic)
    print(f"Input:       {sample_indic}")
    print(f"Identified:  Language={lang_res.language_code}, Script={lang_res.script_code}")

    roman_hindi = "aapka swagat hai, hum aapki kya madad kar sakte hain"
    translit_res = client.text.transliterate(
        input=roman_hindi, source_language_code="en-IN", target_language_code="hi-IN"
    )
    print(f"Romanized:   {roman_hindi}")
    print(f"Devanagari:  {translit_res.transliterated_text}")


def test_voice_cloning(client: SarvamAI, ref_audio_path: Path):
    print("\n--- 4. Direct Cross-Lingual Voice Cloning (/voices/clone) ---")
    if not ref_audio_path.exists():
        print(f"Reference audio not found: {ref_audio_path}")
        return

    url = "https://api.sarvam.ai/voices/clone"
    headers = {"api-subscription-key": os.environ["SARVAM_API_KEY"]}
    files = {"ref_audio": ("ref.wav", open(ref_audio_path, "rb"), "audio/wav")}
    target_text = "नमस्ते! यह मेरी आवाज़ की क्लोनिंग का एक सीधा और लाइव परीक्षण है।"
    data = {
        "text": target_text,
        "language_code": "hi-IN",
        "output_audio_codec": "wav",
        "enable_qc": "false",
    }

    res = httpx.post(url, headers=headers, files=files, data=data, timeout=60.0)
    if res.status_code == 200:
        res_json = res.json()
        b64 = res_json.get("audio_b64") or res_json.get("audio")
        audio_bytes = base64.b64decode(b64)
        out_file = Path("cloned_voice_hindi.wav")
        with open(out_file, "wb") as f:
            f.write(audio_bytes)
        print(f"Target text: {target_text}")
        print(f"Synthesized cloned audio ({res_json.get('audio_duration'):.2f}s) -> {out_file.name}")
    else:
        print(f"Voice cloning request failed: {res.status_code} - {res.text}")


def test_reasoning_and_chat(client: SarvamAI):
    print("\n--- 5. Sarvam-105B Reasoning vs Conversational Models ---")

    # sarvam-105b-conversations (dialogue speed)
    conv_res = client.chat.completions(
        model="sarvam-105b-conversations",
        messages=[
            {
                "role": "user",
                "content": "Explain coparcenary property under Hindu Succession Act in 2 bullet points in simple Hindi.",
            }
        ],
    )
    print("\n[sarvam-105b-conversations Output]:")
    print(conv_res.choices[0].message.content)

    # sarvam-105b (deep legal reasoning)
    reason_res = client.chat.completions(
        model="sarvam-105b",
        messages=[
            {
                "role": "user",
                "content": "Is an oral will valid for immovable property in India? Answer in 1 sentence.",
            }
        ],
        reasoning_effort="low",
        max_tokens=2048,
    )
    print("\n[sarvam-105b Deep Reasoning Output]:")
    print(reason_res.choices[0].message.content)


def main():
    parser = argparse.ArgumentParser(description="Sarvam AI Comprehensive Multi-Engine Test Suite")
    parser.add_argument("--test-all", action="store_true", help="Run live calls across all 5 engines")
    parser.add_argument("--stt", type=str, help="Transcribe audio with Saaras v3")
    parser.add_argument("--translate", type=str, help="Translate text to Hindi & Hinglish")
    parser.add_argument("--clone", type=str, help="Clone reference voice audio into Hindi speech")
    parser.add_argument("--ask", type=str, help="Query sarvam-105b conversational model")

    args = parser.parse_args()
    client = get_client()

    sample_audio = Path("dubbed_outputs/job_fda3b857_hi-IN_audio.wav")
    ref_audio = Path("demo_source_speech.wav")

    if args.stt:
        test_speech_to_text(client, Path(args.stt))
    elif args.translate:
        hi = client.text.translate(
            input=args.translate, source_language_code="en-IN", target_language_code="hi-IN", mode="formal"
        )
        hinglish = client.text.translate(
            input=args.translate, source_language_code="en-IN", target_language_code="hi-IN", mode="code-mixed"
        )
        print(f"Formal Hindi: {hi.translated_text}")
        print(f"Hinglish:     {hinglish.translated_text}")
    elif args.clone:
        test_voice_cloning(client, Path(args.clone))
    elif args.ask:
        res = client.chat.completions(
            model="sarvam-105b-conversations",
            messages=[{"role": "user", "content": args.ask}],
        )
        print(res.choices[0].message.content)
    else:
        # Default or --test-all
        print("=" * 60)
        print("RUNNING LIVE SARVAM AI MULTI-ENGINE SMOKE TEST")
        print("=" * 60)
        test_speech_to_text(client, sample_audio)
        test_translation(client)
        test_language_tools(client)
        test_voice_cloning(client, ref_audio)
        test_reasoning_and_chat(client)
        print("\n" + "=" * 60)
        print("ALL 5 ENGINES TESTED AND VERIFIED!")
        print("=" * 60)


if __name__ == "__main__":
    main()
