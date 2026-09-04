import json
import re

from app.agents.schemas import Diagnosis, PostmortemNarrative

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def extract_json(raw_text: str) -> dict:
    """Extract a JSON object from a model's text response.

    Tolerates the model wrapping the JSON in markdown fences or adding a
    little surrounding prose, since that's a common failure mode even when
    the prompt asks for raw JSON.
    """
    text = raw_text.strip()
    match = _JSON_BLOCK_RE.search(text)
    if not match:
        raise ValueError(f"no JSON object found in model response: {raw_text!r}")
    return json.loads(match.group(0))


def parse_diagnosis(raw_text: str) -> Diagnosis:
    return Diagnosis(**extract_json(raw_text))


def parse_postmortem_narrative(raw_text: str) -> PostmortemNarrative:
    return PostmortemNarrative(**extract_json(raw_text))
