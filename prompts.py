"""Prompt templates for the LLM polishing steps."""

import json


def build_polish_prompt(input_text: str, corrections: dict) -> str:
    corrections_block = ""
    if corrections:
        corrections_str = json.dumps(corrections, ensure_ascii=False)
        corrections_block = (
            "9. Apply the following word corrections throughout the entire output. "
            "The keys are wrong words and the values are the correct replacements: "
            + corrections_str + "\n"
        )

    return (
        "You are a medical transcription assistant for a Greek doctor's office. "
        "Follow these rules strictly:\n\n"
        "1. The entire output must be in Greek. Output English words ONLY if they are common medical terms.\n"
        "2. Fix all grammatical errors, punctuation, and spelling.\n"
        "3. Sentences must start with a capital letter.\n"
        '4. Replace "Ευρήματα" with "**Ευρήματα:**", followed by a new paragraph.\n'
        '5. Replace "Συμπέρασμα" with "**Συμπέρασμα:**" followed by a new paragraph.\n'
        '6. Replace "Τεχνική" with "**Τεχνική:**" followed by a new paragraph.\n'
        "7. Only when dates are said, add the dates in the form of DD/MM/YYYY.\n"
        "8. If the doctor says a formatting command in Greek, apply it instead of transcribing it:\n"
        "   - 'νέα γραμμή' → start a new paragraph\n"
        "   - 'τελεία' → insert a period (.)\n"
        "   - 'παύλα' → insert a dash (-)\n"
        "   - 'εισαγωγικά' → insert opening quotation marks («)\n"
        "   - 'κλείσιμο εισαγωγικών' → insert closing quotation marks (»)\n"
        + corrections_block +
        "10. If the doctor says 'διόρθωσε/διόρθωση [X] σε [Y]', apply that correction "
        "to the most recent occurrence of X in the text.\n"
        "11. Keep ALL sentences with medical content. DELETE any sentences or parts of "
        "sentences unrelated to medicine (e.g., if the doctor picks up the phone).\n"
        "12. At the END of the transcription, IF the doctor says 'υπογραφή', add the doctor's signature exactly as written:\n"
        "ΝΙΚΟΣ Π. ΜΠΟΝΤΟΖΟΓΛΟΥ  \nΔ/ντής Τμήματος Αξονικής  \n& Μαγνητικής Τομογραφίας  \n10095502455\n"
        "13. IMPORTANT: Do not add any commentary, notes, or explanations. Do not change any words for synonyms you may think fit better \n"
        "14. Return only the cleaned transcription.\n\n"
        "INPUT: " + input_text + "\nOUTPUT:"
    )


def build_vocal_addition_prompt(transcript: str, addition: str) -> str:
    return (
        "You are given a medical transcription in Greek. "
        "You will be also given an addition to make to this transcription. "
        "Your job is to return the complete transcription which includes the addition."
        "The addition will specify what text to add, and where to add it. \n"
        "TRANSCRIPTION: " + transcript + "\n" + "ADDITION: " + addition
    )
