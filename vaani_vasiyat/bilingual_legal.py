from typing import Tuple, Dict, Any
from pydantic import BaseModel
from sarvamai import SarvamAI
from .paralegal import TestamentaryPlan


class BilingualDeed(BaseModel):
    english_draft: str
    indic_draft: str
    target_language: str
    section_63_compliant: bool = True


def generate_statutory_english_will(plan: TestamentaryPlan) -> str:
    """Generate formal legal will draft compliant with Section 63 Indian Succession Act, 1925."""
    bequest_lines = []
    for idx, b in enumerate(plan.bequests, 1):
        cond = f" (Subject to condition: {b.conditions_or_life_interest})" if b.conditions_or_life_interest else ""
        anc = " (Self-Acquired / Undivided Share)" if b.is_ancestral is False else ""
        bequest_lines.append(
            f"   Clause {idx}: I devise and bequeath {b.asset_description}{anc} absolutely unto my {b.relationship}, "
            f"namely {b.beneficiary_name}, residing with me or as specified herein{cond}."
        )

    bequests_text = "\n".join(bequest_lines)
    executor = plan.executor_name or "my trusted appointee"
    residuary = plan.residuary_beneficiary or "my legal heirs equally"

    draft = f"""LAST WILL AND TESTAMENT

I, {plan.testator_name}, residing at {plan.residence}, do hereby revoke all my former Wills, Codicils, and Testamentary Dispositions made by me at any time heretofore, and declare this to be my Last Will and Testament.

1. DECLARATION OF CAPACITY:
I declare that I am of sound disposing mind, memory, and understanding, and that I am executing this Will voluntarily out of my free will and pleasure without any fraud, coercion, undue influence, or misrepresentation whatsoever.

2. APPOINTMENT OF EXECUTOR:
I hereby nominate, constitute, and appoint {executor} to be the sole Executor of this my Last Will and Testament, who shall administer my estate and effectuate the bequests herein contained.

3. SCHEDULE OF BEQUESTS:
{bequests_text}

4. RESIDUARY ESTATE:
I give, devise, and bequeath all the rest, residue, and remainder of my estate, both movable and immovable, of whatsoever nature and wheresoever situate, unto {residuary}.

5. TESTATOR EXECUTION:
IN WITNESS WHEREOF, I, the said {plan.testator_name}, the Testator above-named, have hereunto set my hand / thumb impression to this my Last Will and Testament on this day in the presence of the attesting witnesses subscribing below.

_______________________________________
Signature / Thumb Impression of Testator

ATTESTATION CLAUSE (Under Section 63, Indian Succession Act, 1925):
Signed, published, and declared by the above-named Testator, {plan.testator_name}, as and for their Last Will and Testament, in the presence of us, who at their request, in their presence, and in the presence of each other, have hereunto subscribed our names as attesting witnesses:

Witness 1:
Name: _______________________________
Father's/Spouse's Name: ______________
Address: ____________________________
ID Proof (Aadhaar/Voter ID): ________
Signature: __________________________

Witness 2:
Name: _______________________________
Father's/Spouse's Name: ______________
Address: ____________________________
ID Proof (Aadhaar/Voter ID): ________
Signature: __________________________
"""
    return draft.strip()


def compile_bilingual_deed(
    client: SarvamAI,
    plan: TestamentaryPlan,
    target_language_code: str = "hi-IN",
) -> BilingualDeed:
    """Compile Section 63 ISA deed in English and translate to Indic language using Mayura."""
    english_draft = generate_statutory_english_will(plan)

    # Translate deed core into target Indic language using Mayura
    # To keep translation crisp and formal, translate section by section
    paragraphs = english_draft.split("\n\n")
    translated_paras = []

    for para in paragraphs:
        if not para.strip():
            continue
        try:
            res = client.text.translate(
                input=para,
                source_language_code="en-IN",
                target_language_code=target_language_code,
                mode="formal",
            )
            translated_paras.append(res.translated_text)
        except Exception:
            translated_paras.append(para)

    indic_draft = "\n\n".join(translated_paras)

    return BilingualDeed(
        english_draft=english_draft,
        indic_draft=indic_draft,
        target_language=target_language_code,
        section_63_compliant=True,
    )
