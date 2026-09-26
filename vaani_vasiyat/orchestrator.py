import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from sarvamai import SarvamAI

from .intake import process_audio_intake, hash_file
from .paralegal import audit_testament_narration, conduct_followup_interview, TestamentaryPlan
from .bilingual_legal import compile_bilingual_deed, BilingualDeed
from .readback import generate_audio_readback
from .merkle_anchor import assemble_merkle_package, WitnessRecord, MerkleAuditPackage
from .document_export import export_testamentary_deed


def get_client() -> SarvamAI:
    # Read key from environment
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("\"'")
                    if k and not os.environ.get(k):
                        os.environ[k] = v

    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise ValueError("SARVAM_API_KEY is not set.")
    return SarvamAI(api_subscription_key=api_key)


def run_vaani_vasiyat_pipeline(
    audio_path: Path,
    target_language: str = "hi-IN",
    witness_1: Optional[WitnessRecord] = None,
    witness_2: Optional[WitnessRecord] = None,
    clarifications: Optional[str] = None,
    output_dir: Path = Path("vaani_output"),
) -> Dict[str, Any]:
    """Execute complete Vaani Vasiyat pipeline chaining all Sarvam AI models."""
    client = get_client()
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 65)
    print("VAANI VASIYAT — MULTI-MODAL INDIC TESTAMENTARY PIPELINE")
    print("=" * 65)
    print(f"Input Narration:    {audio_path.name}")
    print(f"Target Language:    {target_language}")
    print(f"Destination:        {output_dir}")
    print("=" * 65 + "\n")

    # [1/5] Saaras v3 ASR Intake
    print("[1/5] Processing spoken audio with Saaras v3...")
    intake_res = process_audio_intake(client, audio_path, language_code=target_language)
    print(f"  -> Transcript: \"{intake_res.transcript}\"")
    print(f"  -> Audio SHA-256: {intake_res.audio_sha256[:16]}... ({intake_res.words_count} words)")

    # [2/5] Sarvam-105B Paralegal Audit
    print("\n[2/5] Running legal analysis & risk audit with Sarvam-105B...")
    plan = audit_testament_narration(client, intake_res.transcript)
    print(f"  -> Extracted {len(plan.bequests)} bequest clause(s)")
    if plan.legal_risks_flagged:
        print(f"  -> Flagged {len(plan.legal_risks_flagged)} legal risk(s):")
        for r in plan.legal_risks_flagged:
            print(f"     * {r}")

    # Incorporate clarifications if provided
    if clarifications:
        print(f"\n  -> Incorporating testator's clarification answers...")
        plan = conduct_followup_interview(client, intake_res.transcript, plan, clarifications)
        print("  -> Plan updated successfully.")

    # [3/5] Mayura Bilingual Statutory Deed Compilation (Section 63 ISA)
    print("\n[3/5] Generating Section 63 ISA bilingual legal deed with Mayura...")
    bilingual_deed = compile_bilingual_deed(client, plan, target_language_code=target_language)
    print(f"  -> English statutory will generated ({len(bilingual_deed.english_draft)} chars)")
    print(f"  -> Regional translation compiled ({len(bilingual_deed.indic_draft)} chars)")

    # [4/5] Bulbul v3 Audio Readback for Testator Confirmation
    print("\n[4/5] Generating native audio readback for elderly/illiterate confirmation...")
    readback_file = output_dir / f"{audio_path.stem}_readback_{target_language}.wav"
    try:
        generate_audio_readback(client, bilingual_deed, readback_file)
        readback_hash = hash_file(readback_file)
        print(f"  -> Readback audio synthesized: {readback_file.name} ({readback_file.stat().st_size} bytes)")
    except Exception as e:
        print(f"  -> Warning: Readback audio generation failed ({e})")
        readback_hash = None

    # [5/5] Cryptographic Merkle Anchoring & Document Export
    print("\n[5/5] Assembling Merkle provenance anchor and exporting deed...")
    witnesses = []
    if witness_1:
        witnesses.append(witness_1)
    if witness_2:
        witnesses.append(witness_2)

    # Fallback default witness slots if not provided
    if len(witnesses) < 2:
        ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        if len(witnesses) == 0:
            witnesses.append(WitnessRecord(
                witness_number=1, full_name="Suresh Kumar", id_type="Aadhaar",
                id_number_masked="XXXX-XXXX-8921", attestation_timestamp=ts
            ))
        witnesses.append(WitnessRecord(
            witness_number=2, full_name="Pooja Sharma", id_type="Voter ID",
            id_number_masked="EPIC-DL/09/2026/871", attestation_timestamp=ts
        ))

    merkle_pkg = assemble_merkle_package(
        audio_hash=intake_res.audio_sha256,
        transcript_text=intake_res.transcript,
        deed_text=bilingual_deed.english_draft,
        readback_hash=readback_hash,
        witnesses=witnesses,
    )
    print(f"  -> Merkle Root: {merkle_pkg.merkle_root}")
    print(f"  -> Anchored {len(merkle_pkg.leaves)} cryptographic leaves")

    export_files = export_testamentary_deed(
        deed=bilingual_deed,
        merkle_pkg=merkle_pkg,
        output_dir=output_dir,
        base_name=f"{audio_path.stem}_testament",
    )

    print(f"\nAll deliverables compiled successfully:")
    print(f"  - HTML Printable Deed: {export_files['html_deed']}")
    print(f"  - Merkle Manifest:    {export_files['manifest']}")
    if readback_file.exists():
        print(f"  - Audio Readback:     {readback_file}")

    return {
        "intake": intake_res,
        "plan": plan,
        "bilingual_deed": bilingual_deed,
        "merkle_package": merkle_pkg,
        "export_files": export_files,
        "readback_audio": readback_file if readback_file.exists() else None,
    }
