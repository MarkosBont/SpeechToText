from openai import OpenAI
from filelock import FileLock
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_MED_API_KEY"))
CORRECTIONS_FILE = "corrections.json"
CORRECTIONS_LOCK = "corrections.json.lock"

def load_corrections() -> dict:
    if not os.path.exists(CORRECTIONS_FILE):
        return {}
    with FileLock(CORRECTIONS_LOCK):
        with open(CORRECTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)



def openai_call(input:str):
    corrections_str = json.dumps(load_corrections(), ensure_ascii=False)

    if corrections_str == "{}":
        response = client.responses.create(
            model="gpt-5",
            input=(
                "You are a medical transcription assistant for a Greek doctor's office. Follow these rules strictly:\n\n"
                "1. The entire output must be in Greek. Output English words ONLY if they are common medical terms.\n"
                "2. Fix all grammatical errors, punctuation, and spelling.\n"
                "3. Sentences must start with a capital letter.\n"
                "4. If the doctor says a formatting command in Greek, apply it instead of transcribing it:\n"
                    "   - 'παράγραφος' → start a new paragraph\n"
                    "   - 'τελεία' → insert a period (.)\n"
                    "   - 'ερωτηματικό' → insert a question mark (;)\n"
                    "   - 'παύλα' → insert a dash (-)\n"
                    "   - 'εισαγωγικά' → insert opening quotation marks («)\n"
                    "   - 'κλείσιμο εισαγωγικών' → insert closing quotation marks (»)\n"
                    "5. If the doctor says 'διόρθωσε/διόρθωση [X] σε [Y]', apply that correction to the most recent occurrence of X in the text.\n"
                    "6. Keep ALL sentences with medical content. DELETE any sentences or parts of sentences unrelated to medicine (e.g., if the doctor picks up the phone).\n"
                    "7. Do not add any commentary, notes, or explanations. Return only the cleaned transcription.\n\n"
                    "INPUT: " + input + "\nOUTPUT:"
            ))
        return response.output_text

    else:
        response = client.responses.create(
            model="gpt-5",
            input=(
                    "You are a medical transcription assistant for a Greek doctor's office. Follow these rules strictly:\n\n"
                    "1. The entire output must be in Greek. Output English words ONLY if they are common medical terms.\n"
                    "2. Fix all grammatical errors, punctuation, and spelling.\n"
                    "3. Sentences must start with a capital letter.\n"
                    "4. Apply the following word corrections throughout the entire output. The keys are wrong words and the values are the correct replacements: " + corrections_str + "\n"
                                                                                                                                                                                       "5. If the doctor says a formatting command in Greek, apply it instead of transcribing it:\n"
                                                                                                                                                                                       "   - 'παράγραφος' → start a new paragraph\n"
                                                                                                                                                                                       "   - 'τελεία' → insert a period (.)\n"
                                                                                                                                                                                       "   - 'ερωτηματικό' → insert a question mark (;)\n"
                                                                                                                                                                                       "   - 'παύλα' → insert a dash (-)\n"
                                                                                                                                                                                       "   - 'εισαγωγικά' → insert opening quotation marks («)\n"
                                                                                                                                                                                       "   - 'κλείσιμο εισαγωγικών' → insert closing quotation marks (»)\n"
                                                                                                                                                                                       "6. If the doctor says 'διόρθωσε/διόρθωση [X] σε [Y]', apply that correction to the most recent occurrence of X in the text.\n"
                                                                                                                                                                                       "7. Keep ALL sentences with medical content. DELETE any sentences or parts of sentences unrelated to medicine (e.g., if the doctor picks up the phone).\n"
                                                                                                                                                                                       "8. Do not add any commentary, notes, or explanations. Return only the cleaned transcription.\n\n"
                                                                                                                                                                                       "INPUT: " + input + "\nOUTPUT:"
            ))
        return response.output_text
