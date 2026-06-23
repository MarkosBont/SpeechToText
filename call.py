from openai import OpenAI
from supabase import create_client
import os
import json
from dotenv import load_dotenv


load_dotenv()

key = os.getenv("OPENAI_MED_API_KEY")
client = OpenAI(api_key=key)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_API_KEY"))


def load_corrections() -> dict:
    response = supabase.table("Corrections").select("wrong, correct").execute()
    return {row["wrong"]: row["correct"] for row in response.data}


def build_prompt(input_text: str, corrections: dict) -> str:
    corrections_block = ""
    if corrections:
        corrections_str = json.dumps(corrections, ensure_ascii=False)
        corrections_block = (
            "8. Apply the following word corrections throughout the entire output. "
            "The keys are wrong words and the values are the correct replacements: "
            + corrections_str + "\n"
        )

    return (
        "You are a medical transcription assistant for a Greek doctor's office. "
        "Follow these rules strictly:\n\n"
        "1. The entire output must be in Greek. Output English words ONLY if they are common medical terms.\n"
        "2. Fix all grammatical errors, punctuation, and spelling.\n"
        "3. Sentences must start with a capital letter.\n"
        "4. If the following word is said: Ευρήματα, replace it with this format: **Eυρήματα:**.\n"
        "5. If the following word is said: Συμπέρασμα, replace it with this format: **Συμπέρασμα:**.\n"
        "6. Only when dates are said, add the dates in the form of XX/XX/XXXX.\n"
        "7. If the doctor says a formatting command in Greek, apply it instead of transcribing it:\n"
        "   - 'παράγραφος' → start a new paragraph\n"
        "   - 'τελεία' → insert a period (.)\n"
        "   - 'ερωτηματικό' → insert a question mark (;)\n"
        "   - 'παύλα' → insert a dash (-)\n"
        "   - 'εισαγωγικά' → insert opening quotation marks («)\n"
        "   - 'κλείσιμο εισαγωγικών' → insert closing quotation marks (»)\n"
        + corrections_block +
        "9. If the doctor says 'διόρθωσε/διόρθωση [X] σε [Y]', apply that correction "
        "to the most recent occurrence of X in the text.\n"
        "10. Keep ALL sentences with medical content. DELETE any sentences or parts of "
        "sentences unrelated to medicine (e.g., if the doctor picks up the phone).\n"
        "IMPORTANT: Do not add any commentary, notes, or explanations. "
        "Return only the cleaned transcription.\n\n"
        "INPUT: " + input_text + "\nOUTPUT:"
    )


def openai_call(input: str) -> str:
    if not input or not input.strip():
        return "Error: empty input"

    corrections = load_corrections()
    prompt = build_prompt(input, corrections)

    try:
        response = client.responses.create(
            model="gpt-5.5",
            input=prompt,
            max_output_tokens=10000
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