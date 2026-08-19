"""OpenAI text-polishing calls (transcript cleanup + vocal additions)."""

from config import openai_client as client
from database import load_corrections
from prompts import build_polish_prompt, build_vocal_addition_prompt


def _run_completion(prompt: str, **extra) -> str:
    try:
        response = client.responses.create(
            model="gpt-5.5",
            input=prompt,
            max_output_tokens=10000,
            **extra,
        )
    except Exception as e:
        return f"API error: {e}"

    if getattr(response, "status", None) == "incomplete":
        details = getattr(response, "incomplete_details", None)
        reason = getattr(details, "reason", "unknown") if details else "unknown"
        return f"Incomplete response: {reason}"

    if response.output_text:
        return response.output_text

    return "Empty output — model returned no text (possible refusal or reasoning-only response)"


def openai_call(user_id: str, input_text: str) -> str:
    if not input_text or not input_text.strip():
        return "Error: empty input"

    corrections = load_corrections(user_id)
    prompt = build_polish_prompt(input_text, corrections)
    return _run_completion(prompt, reasoning={"effort": "none"})


def openai_call_vocal_addition(user_id: str, transcript: str, addition: str) -> str:
    prompt = build_vocal_addition_prompt(transcript, addition)
    return _run_completion(prompt)
