"""All Supabase reads/writes, scoped by user_id."""

from config import supabase_client as supabase


def load_corrections(user_id: str) -> dict:
    response = (
        supabase.table("Corrections")
        .select("wrong, correct")
        .eq("user_id", user_id)
        .execute()
    )
    return {row["wrong"]: row["correct"] for row in response.data}


def save_correction(user_id: str, wrong: str, correct: str) -> None:
    supabase.table("Corrections").insert(
        {"user_id": user_id, "wrong": wrong, "correct": correct}
    ).execute()


def delete_correction(user_id: str, wrong: str) -> None:
    supabase.table("Corrections").delete().eq("user_id", user_id).eq("wrong", wrong).execute()


def save_transcription(user_id: str, whisper_transcript: str, polished_transcript: str) -> None:
    supabase.table("transcriptions").insert(
        {
            "user_id": user_id,
            "whisper_transcript": whisper_transcript,
            "polished_transcript": polished_transcript,
        }
    ).execute()


def save_addition(user_id: str, addition_transcript: str, polished_transcript: str) -> None:
    supabase.table("transcriptions").insert(
        {
            "user_id": user_id,
            "whisper_transcript": addition_transcript,
            "polished_transcript": polished_transcript,
            "vocal_addition": True,
        }
    ).execute()


def latest_polished(user_id: str) -> str:
    resp = (
        supabase.table("transcriptions")
        .select("polished_transcript")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return resp.data[0]["polished_transcript"] if resp.data else ""
