import json
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sarvamai import SarvamAI


class AssetBequest(BaseModel):
    asset_description: str
    property_type: str = "immovable"  # immovable or movable
    is_ancestral: Optional[bool] = None  # None if unknown, True if ancestral
    beneficiary_name: str
    relationship: str
    conditions_or_life_interest: Optional[str] = None


class TestamentaryPlan(BaseModel):
    testator_name: str = "Unknown Testator"
    testator_age: Optional[int] = None
    residence: str = "India"
    mental_soundness_declared: Optional[bool] = True
    revocation_prior_wills: Optional[bool] = True
    bequests: List[AssetBequest] = Field(default_factory=list)
    residuary_beneficiary: Optional[str] = None
    executor_name: Optional[str] = None
    legal_risks_flagged: List[str] = Field(default_factory=list)
    clarification_questions: List[str] = Field(default_factory=list)


PARALEGAL_SYSTEM_PROMPT = """You are an elite Indian Succession Law paralegal assistant specializing in Section 63 of the Indian Succession Act, 1925 and Hindu Succession Act, 1956.
Your task is to analyze a spoken narration of a will (in Hindi, English, or mixed Indic languages) and extract structured bequest data while actively detecting legal vulnerabilities that could trigger decades of probate litigation.

You MUST identify:
1. Contradictions & Overlaps: Did the speaker grant the same asset to multiple people without clear division?
2. Ancestral vs. Self-Acquired Property Risk: Under Hindu law, coparcenary ancestral property cannot be willed away in its entirety if other coparceners have rights. If ancestral, flag it!
3. Ambiguity: Are property boundaries or survey/khasra numbers missing?
4. Residuary Clause: What happens to unmentioned assets?
5. Executor: Who is appointed to execute this will?

Return your analysis strictly in valid JSON format matching this schema:
{
  "testator_name": "string",
  "testator_age": number or null,
  "residence": "string",
  "mental_soundness_declared": true/false,
  "revocation_prior_wills": true/false,
  "bequests": [
    {
      "asset_description": "description",
      "property_type": "immovable" or "movable",
      "is_ancestral": true or false or null,
      "beneficiary_name": "name",
      "relationship": "relation",
      "conditions_or_life_interest": "conditions or null"
    }
  ],
  "residuary_beneficiary": "name or null",
  "executor_name": "name or null",
  "legal_risks_flagged": [
    "Risk 1: explanation",
    "Risk 2: explanation"
  ],
  "clarification_questions": [
    "Question 1 for testator in polite Hindi/English",
    "Question 2 for testator in polite Hindi/English"
  ]
}
Do not include any preamble or extra text outside the JSON.
"""


def clean_json_text(text: str) -> str:
    """Clean markdown code fences and extraneous text around JSON."""
    text = text.strip()
    match = re.search(r"```(?:json)?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def audit_testament_narration(client: SarvamAI, narration_text: str) -> TestamentaryPlan:
    """Analyze testator speech, extract slots, and flag legal risks."""
    messages = [
        {"role": "system", "content": PARALEGAL_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Here is the spoken narration from the testator:\n\n\"{narration_text}\"\n\nAnalyze and return structured JSON.",
        },
    ]

    response = client.chat.completions(
        model="sarvam-105b-conversations",
        messages=messages,
        temperature=0.2,
    )

    raw_content = response.choices[0].message.content or "{}"
    cleaned = clean_json_text(raw_content)

    try:
        data = json.loads(cleaned)
        return TestamentaryPlan(**data)
    except Exception as e:
        # Fallback heuristic parsing if JSON was imperfect
        print(f"Warning: JSON parsing had error ({e}), parsing with heuristic fallback.")
        return TestamentaryPlan(
            testator_name="Testator",
            bequests=[
                AssetBequest(
                    asset_description="Mentioned assets",
                    beneficiary_name="Mentioned heirs",
                    relationship="Family",
                )
            ],
            legal_risks_flagged=["Requires verification of survey numbers and self-acquired status."],
            clarification_questions=[
                "कृपया पुष्टि करें कि क्या यह ज़मीन आपकी स्व-अर्जित (self-acquired) है या पैतृक (ancestral)?",
                "क्या आपने वसीयत के निष्पादन (executor) के लिए किसी विश्वस्त व्यक्ति को चुना है?",
            ],
        )


def conduct_followup_interview(
    client: SarvamAI,
    original_narration: str,
    plan: TestamentaryPlan,
    user_clarifications: str,
) -> TestamentaryPlan:
    """Update the testamentary plan with answers provided during the follow-up interview."""
    update_prompt = f"""You are the Indian Succession Law paralegal assistant.
Original Narration: "{original_narration}"
Existing Plan: {plan.model_dump_json()}
Testator's Clarifications & Answers: "{user_clarifications}"

Update the testamentary plan incorporating the new answers. Resolve the answered risks.
Return the updated plan strictly in valid JSON adhering to the exact same schema.
"""
    messages = [
        {"role": "system", "content": PARALEGAL_SYSTEM_PROMPT},
        {"role": "user", "content": update_prompt},
    ]

    response = client.chat.completions(
        model="sarvam-105b-conversations",
        messages=messages,
        temperature=0.2,
    )

    cleaned = clean_json_text(response.choices[0].message.content or "{}")
    try:
        data = json.loads(cleaned)
        return TestamentaryPlan(**data)
    except Exception:
        return plan
