"""
Intent classifier.

Classifies user utterances into FRIDAY architecture intent types:
  CHAT | PICK | PLACE | GIVE | FIND | MOVE_ARM

Mirrors friday_interfaces/msg/Intent.msg (confidence omitted).
Runs in its own thread parallel to the LLM conversation thread.
"""

import json
import re
from dataclasses import dataclass, field

import requests

from config import OLLAMA_URL, INTENT_MODEL, INTENT_TIMEOUT

_VALID_TYPES = {"CHAT", "PICK", "PLACE", "GIVE", "FIND", "MOVE_ARM"}

_GENERATE_URL = f"{OLLAMA_URL}/api/generate"

_SYSTEM_PROMPT = (
    "You are an intent classifier for FRIDAY, an AI robotic arm desk assistant.\n"
    "Classify the user message into exactly one intent_type:\n"
    "  CHAT     - general conversation, questions, anything needing only a spoken reply\n"
    "  FIND     - locate an object: 'where is my pen?', 'can you see the notebook?'\n"
    "  PICK     - pick up an object: 'pick up the cup'\n"
    "  PLACE    - place an object somewhere: 'put the pen on the left'\n"
    "  GIVE     - hand an object to the user: 'give me the notebook', 'pass the stapler'\n"
    "  MOVE_ARM - direct arm movement: 'move your arm left', 'point at the screen'\n\n"
    "Extract target_object: the object name (e.g. 'pen', 'cup') or empty string if not applicable.\n\n"
    "Respond with ONLY valid JSON - no markdown, no explanation:\n"
    '{"intent_type":"CHAT"|"PICK"|"PLACE"|"GIVE"|"FIND"|"MOVE_ARM","target_object":"name or empty string"}'
)


# -- Result type --------------------------------------------------------------

@dataclass
class IntentResult:
    """Mirrors friday_interfaces/msg/Intent.msg."""
    intent_type:   str         # CHAT | PICK | PLACE | GIVE | FIND | MOVE_ARM
    raw_text:      str         # original user utterance (passed through unchanged)
    target_object: str = field(default="")  # object label, e.g. "pen"; "" for CHAT


# -- Parser -------------------------------------------------------------------

class IntentParser:
    """
    Classify a user utterance via a non-streaming Ollama call.

    Uses a lightweight model (INTENT_MODEL) for speed.
    Falls back to CHAT intent on any error so Friday always replies.
    """

    def parse(self, text: str) -> IntentResult:
        try:
            resp = requests.post(
                _GENERATE_URL,
                json={
                    "model":   INTENT_MODEL,
                    "system":  _SYSTEM_PROMPT,
                    "prompt":  text,
                    "stream":  False,
                    "options": {"temperature": 0, "num_predict": 60},
                },
                timeout=INTENT_TIMEOUT,
            )
            resp.raise_for_status()
            raw   = resp.json().get("response", "").strip()
            match = re.search(r"\{.*?\}", raw, re.DOTALL)
            if match:
                data        = json.loads(match.group())
                intent_type = data.get("intent_type", "CHAT").upper()
                if intent_type not in _VALID_TYPES:
                    intent_type = "CHAT"
                return IntentResult(
                    intent_type   = intent_type,
                    raw_text      = text,
                    target_object = (data.get("target_object") or "").strip(),
                )
        except Exception as exc:
            print(f"[Intent] Classification error: {exc}")

        # Safe fallback: always reply as conversation
        return IntentResult(intent_type="CHAT", raw_text=text)
