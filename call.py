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



def openai_call(input:str):
    corrections_str = json.dumps(load_corrections(), ensure_ascii=False)

    if corrections_str == "{}":
        response = client.responses.create(
            model="gpt-5.0",
            input=(
                "You are a medical transcription assistant for a Greek doctor's office. Follow these rules strictly:\n\n"
                "1. The entire output must be in Greek. Output English words ONLY if they are common medical terms.\n"
                "2. Fix all grammatical errors, punctuation, and spelling.\n"
                "3. Sentences must start with a capital letter.\n"
                "4. If the following word is said: Ευρήματα, replace it with this format: **Eυρήματα:**.\n"
                "5. If the following word is said: Συμπέρασμα, replace it with this format: **Συμπέρασμα:**.\n"
                "6. Always add dates in the form of XX/XX/XXXX>>\n"
                "7. If the doctor says a formatting command in Greek, apply it instead of transcribing it:\n"
                    "   - 'παράγραφος' → start a new paragraph\n"
                    "   - 'τελεία' → insert a period (.)\n"
                    "   - 'ερωτηματικό' → insert a question mark (;)\n"
                    "   - 'παύλα' → insert a dash (-)\n"
                    "   - 'εισαγωγικά' → insert opening quotation marks («)\n"
                    "   - 'κλείσιμο εισαγωγικών' → insert closing quotation marks (»)\n"
                    "8. If the doctor says 'διόρθωσε/διόρθωση [X] σε [Y]', apply that correction to the most recent occurrence of X in the text.\n"
                    "9. Keep ALL sentences with medical content. DELETE any sentences or parts of sentences unrelated to medicine (e.g., if the doctor picks up the phone).\n"
                    "IMPORTANT: Do not add any commentary, notes, or explanations. Return only the cleaned transcription.\n\n"
                    "INPUT: " + input + "\nOUTPUT:"
            ))
        if response.output_text:
            return response.output_text
        else:
            return "Error with API Response"

    else:
        response = client.responses.create(
            model="gpt-5.0",
            input=(
                    "You are a medical transcription assistant for a Greek doctor's office. Follow these rules strictly:\n\n"
                    "1. Always output the words: ευρήματα and συμπέρασμα in this format: **Ευρήματα:** and **Συμπέρασμα:**.\n"
                    "1. The entire output must be in Greek. Output English words ONLY if they are common medical terms.\n"
                    "2. Fix all grammatical errors, punctuation, and spelling.\n"
                    "3. Sentences must start with a capital letter.\n"
                    "4. If the following word is said: Συμπέρασμα, replace it with this format: **Συμπέρασμα:**.\n"
                    "5. If the doctor says a formatting command in Greek, apply it instead of transcribing it:\n"
                    "6. Always add dates in the form of XX/XX/XXXX>>\n"
                    "7. Apply the following word corrections throughout the entire output. The keys are wrong words and the values are the correct replacements: " + corrections_str + "\n"
                                                                                                                                                                                       "8. If the doctor says a formatting command in Greek, apply it instead of transcribing it:\n"
                                                                                                                                                                                       "   - 'παράγραφος' → start a new paragraph\n"
                                                                                                                                                                                       "   - 'τελεία' → insert a period (.)\n"
                                                                                                                                                                                       "   - 'ερωτηματικό' → insert a question mark (;)\n"
                                                                                                                                                                                       "   - 'παύλα' → insert a dash (-)\n"
                                                                                                                                                                                       "   - 'εισαγωγικά' → insert opening quotation marks («)\n"
                                                                                                                                                                                       "   - 'κλείσιμο εισαγωγικών' → insert closing quotation marks (»)\n"
                                                                                                                                                                                       "9. If the doctor says 'διόρθωσε/διόρθωση [X] σε [Y]', apply that correction to the most recent occurrence of X in the text.\n"
                                                                                                                                                                                       "10. Keep ALL sentences with medical content. DELETE any sentences or parts of sentences unrelated to medicine (e.g., if the doctor picks up the phone).\n"
                                                                                                                                                                                       "IMPORTANT: DO NOT ADD ANY COMMENTARY, NOTES, OR EXPLANATIONS OF YOUR OWN! Return only the cleaned transcription.\n\n"
                                                                                                                                                                                       "INPUT: " + input + "\nOUTPUT:"
            ))
        if response.output_text:
            return response.output_text
        else:
            return "Error with API Response"
