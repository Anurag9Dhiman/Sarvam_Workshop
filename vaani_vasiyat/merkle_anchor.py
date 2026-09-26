import hashlib
import json
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class WitnessRecord(BaseModel):
    witness_number: int  # 1 or 2
    full_name: str
    id_type: str  # Aadhaar, EPIC, PAN
    id_number_masked: str
    attestation_timestamp: str


class MerkleLeaf(BaseModel):
    index: int
    label: str
    hash_value: str


class MerkleAuditPackage(BaseModel):
    package_id: str
    created_at_utc: str
    merkle_root: str
    leaves: List[MerkleLeaf]
    witnesses: List[WitnessRecord]
    section_63_isa_compliance: bool = True
    bsa_section_63_electronic_evidence_certified: bool = True


def sha256_str(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_merkle_root(leaf_hashes: List[str]) -> str:
    """Compute standard cryptographic Merkle root from list of leaf hashes."""
    if not leaf_hashes:
        return ""
    current_level = leaf_hashes[:]
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            combined = hashlib.sha256((left + right).encode("utf-8")).hexdigest()
            next_level.append(combined)
        current_level = next_level
    return current_level[0]


def assemble_merkle_package(
    audio_hash: str,
    transcript_text: str,
    deed_text: str,
    readback_hash: Optional[str],
    witnesses: List[WitnessRecord],
) -> MerkleAuditPackage:
    """Assemble all digital and physical attestation artifacts into a Merkle root package."""
    leaves: List[MerkleLeaf] = []

    # Leaf 1: Raw Voice Recording
    leaves.append(MerkleLeaf(index=0, label="Raw Voice Recording (Audio Hash)", hash_value=audio_hash))

    # Leaf 2: Saaras Transcript
    transcript_hash = sha256_str(transcript_text)
    leaves.append(MerkleLeaf(index=1, label="Saaras Dialect Transcript", hash_value=transcript_hash))

    # Leaf 3 & 4: Witnesses
    for idx, w in enumerate(witnesses, start=len(leaves)):
        w_hash = sha256_str(w.model_dump_json())
        leaves.append(MerkleLeaf(index=idx, label=f"Witness {w.witness_number} ({w.full_name})", hash_value=w_hash))

    # Leaf 5: Legal Deed Text
    deed_hash = sha256_str(deed_text)
    leaves.append(MerkleLeaf(index=len(leaves), label="Bilingual Legal Will Deed", hash_value=deed_hash))

    # Leaf 6: Audio Readback Confirmation (if present)
    if readback_hash:
        leaves.append(MerkleLeaf(index=len(leaves), label="Bulbul Audio Readback Confirmation", hash_value=readback_hash))

    leaf_hashes = [leaf.hash_value for leaf in leaves]
    merkle_root = compute_merkle_root(leaf_hashes)

    package_id = f"VV-MKL-{int(time.time())}-{merkle_root[:8]}"

    return MerkleAuditPackage(
        package_id=package_id,
        created_at_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        merkle_root=merkle_root,
        leaves=leaves,
        witnesses=witnesses,
        section_63_isa_compliance=len(witnesses) >= 2,
        bsa_section_63_electronic_evidence_certified=True,
    )
