import json
import re

from app.agents.schemas import Diagnosis

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def parse_diagnosis(raw_text: str) -> Diagnosis:
    """Extract a Diagnosis JSON object from a model's final text response.

    Tolerates the model wrapping the JSON in markdown fences or adding a
    little surrounding prose, since that's a common failure mode even when
    the prompt asks for raw JSON.
    """
    text = raw_text.strip()
    match = _JSON_BLOCK_RE.search(text)
    if not match:
        raise ValueError(f"no JSON object found in model response: {raw_text!r}")

    data = json.loads(match.group(0))
    return Diagnosis(**data)
