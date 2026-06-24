import streamlit as st
import tempfile
import os
import time
from datetime import datetime
from supabase import create_client
from audiorecorder import audiorecorder
from call import openai_call, openai_call_vocal_addition
from openai import OpenAI
from dotenv import load_dotenv
import streamlit.components.v1 as components

load_dotenv()

# ── Supabase ──────────────────────────────────────────────────────────────────
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_API_KEY"))

def load_corrections() -> dict:
    response = supabase.table("Corrections").select("wrong, correct").execute()
    return {row["wrong"]: row["correct"] for row in response.data}

def save_correction(wrong: str, correct: str):
    supabase.table("Corrections").upsert({"wrong": wrong, "correct": correct}).execute()

def delete_correction(wrong: str):
    supabase.table("Corrections").delete().eq("wrong", wrong).execute()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Speech to Text", page_icon="🎙️", layout="centered")

if "last_transcript" not in st.session_state:
    st.session_state.last_transcript = ""
if "last_status" not in st.session_state:
    st.session_state.last_status = None
if "last_polished" not in st.session_state:
    st.session_state.last_polished = ""
if "base_polished" not in st.session_state:
    st.session_state.base_polished = ""
if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None
if "correction_msg" not in st.session_state:
    st.session_state.correction_msg = None
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "main_recorder_key" not in st.session_state:
    st.session_state.main_recorder_key = 0
if "vocal_recorder_key" not in st.session_state:
    st.session_state.vocal_recorder_key = 0
if "vocal_msg" not in st.session_state:
    st.session_state.vocal_msg = None

# ── Progress helper ───────────────────────────────────────────────────────────
def advance_progress(progress_bar, current: int, target: int, step_delay: float = 0.02):
    for val in range(current, target + 1):
        progress_bar.progress(val)
        time.sleep(step_delay)
    return target

# ── Core functions ────────────────────────────────────────────────────────────
client = OpenAI(api_key=os.getenv("OPENAI_MED_API_KEY"))

def transcribe(audio_bytes: bytes, progress_bar, status_text):
    tmp_path = None
    try:
        current = 0
        status_text.markdown("**⚙ Προετοιμασία αρχείου…**")
        current = advance_progress(progress_bar, current, 10)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        status_text.markdown("**Μεταγραφή ομιλίας...**")
        current = advance_progress(progress_bar, current, 30)

        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="el"
            )
        text = result.text.strip()

        status_text.markdown("**Μεταγραφή ολοκληρώθηκε.**")
        current = advance_progress(progress_bar, current, 60)

        return (text, "ok", current) if text else ("Δεν εντοπίστηκε ομιλία.", "unknown", current)
    except Exception as e:
        return f"Σφάλμα: {e}", "error", 0
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

def polish(transcript: str, progress_bar, status_text, current: int):
    status_text.markdown("**Polishing Text…**")
    current = advance_progress(progress_bar, current, 75)

    result = openai_call(transcript)

    status_text.markdown("**Απάντηση ελήφθη.**")
    current = advance_progress(progress_bar, current, 95)

    return result, current

def vocal_addition(transcript: str, addition: str, progress_bar, status_text, current: int):
    status_text.markdown("**Polishing Text…**")
    current = advance_progress(progress_bar, current, 75)

    result = openai_call_vocal_addition(transcript, addition)

    status_text.markdown("**Απάντηση ελήφθη.**")
    current = advance_progress(progress_bar, current, 95)

    return result, current

# ── Centering helper for the audiorecorder widgets ────────────────────────────
def center_recorders():
    components.html(
        """
        <script>
        const doc = window.parent.document;
        const apply = () => {
            [...doc.querySelectorAll('iframe')]
                .filter(f => (f.title || '').toLowerCase().includes('audiorecorder'))
                .forEach(f => {
                    f.style.width = '100%';
                    f.style.display = 'block';
                    try {
                        const d = f.contentDocument;
                        if (d && d.body) {
                            d.body.style.margin = '0';
                            d.body.style.display = 'flex';
                            d.body.style.justifyContent = 'center';
                            d.body.style.width = '100%';
                        }
                    } catch (e) {}
                });
        };
        apply();
        let n = 0;
        const t = setInterval(() => { apply(); if (++n > 15) clearInterval(t); }, 300);
        </script>
        """,
        height=0,
    )

# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='text-align: center;'>Medical Transcription</h1>", unsafe_allow_html=True)
st.divider()

st.subheader('Main Recording')
# ── Main recorder ─────────────────────────────────────────────────────────────
audio = audiorecorder(
    "", "", "",
    show_visualizer=True,
    key=f"recorder_{st.session_state.main_recorder_key}",
)
center_recorders()



if len(audio) > 0:
    wav_buffer = audio.export(format="mp3")
    audio_bytes = wav_buffer.read()
    st.session_state.last_audio_bytes = audio_bytes

    progress_bar = st.progress(0)
    status_text  = st.empty()

    transcript, status, current = transcribe(audio_bytes, progress_bar, status_text)
    st.session_state.last_transcript = transcript
    st.session_state.last_status     = status
    st.session_state.vocal_msg       = None   # new transcription clears stale addition msg

    if status != "error":
        polished_transcript, current = polish(transcript, progress_bar, status_text, current)
        st.session_state.last_polished = polished_transcript
        st.session_state.base_polished = polished_transcript   # un-merged baseline for additions
        advance_progress(progress_bar, current, 100)
        status_text.markdown("**Έτοιμο!**")
    else:
        st.session_state.last_polished = transcript

    # consume this recording: refresh the main recorder so it can't reprocess,
    # and refresh the vocal recorder so the new transcription gets a clean,
    # empty addition recorder (mic shows, no stale state).
    st.session_state.main_recorder_key  += 1
    st.session_state.vocal_recorder_key += 1
    st.rerun()

if st.session_state.last_status is not None:
    st.divider()
    status   = st.session_state.last_status
    polished = st.session_state.last_polished

    if status == "ok":
        if st.session_state.last_audio_bytes:
            st.audio(st.session_state.last_audio_bytes, format="audio/mp3")

        st.markdown(polished)
        st.download_button(
            "⬇ Download .txt",
            data=polished,
            file_name=f"transcript_{datetime.now().strftime('%H%M%S')}.txt",
            mime="text/plain",
            key="download_main",
        )

        # ── Vocal addition ───────────────────────────────────────────────────
        st.subheader("Vocal Addition")

        audio_addition = audiorecorder(
            "", "", "",
            show_visualizer=True,
            key=f"vocal_recorder_{st.session_state.vocal_recorder_key}",
        )
        center_recorders()

        if len(audio_addition) > 0:
            wav_buffer = audio_addition.export(format="mp3")
            audio_bytes = wav_buffer.read()

            progress_bar = st.progress(0)
            status_text = st.empty()

            addition_transcript, add_status, current = transcribe(audio_bytes, progress_bar, status_text)

            if add_status == "ok":
                transcript_with_addition, current = vocal_addition(
                    st.session_state.base_polished, addition_transcript,
                    progress_bar, status_text, current
                )
                st.session_state.last_polished = transcript_with_addition
                advance_progress(progress_bar, current, 100)
                status_text.markdown("**Έτοιμο!**")
            elif add_status == "unknown":
                st.session_state.vocal_msg = ("warning", addition_transcript)
            else:
                st.session_state.vocal_msg = ("error", addition_transcript)

            # consume this recording: recreate the recorder empty so it can't be
            # reprocessed and is ready for the next addition
            st.session_state.vocal_recorder_key += 1
            st.rerun()

        if st.session_state.vocal_msg:
            kind, text = st.session_state.vocal_msg
            getattr(st, kind)(text)
            st.session_state.vocal_msg = None


    elif status == "unknown":
        st.warning(polished)
    else:
        st.error(polished)


# ── Corrections manager ───────────────────────────────────────────────────────
corrections = load_corrections()

st.subheader("Add a Correction")
col_a, col_b, col_c = st.columns([2, 2, 1])
wrong_word   = col_a.text_input("Wrong word",   key=f"new_wrong_{st.session_state.input_key}",   label_visibility="collapsed", placeholder="Wrong word")
correct_word = col_b.text_input("Correct word", key=f"new_correct_{st.session_state.input_key}", label_visibility="collapsed", placeholder="Correct word")

if col_c.button("Add"):
    if wrong_word.strip() and correct_word.strip():
        save_correction(wrong_word.strip(), correct_word.strip())
        st.session_state.correction_msg = f"Added: '{wrong_word}' → '{correct_word}'"
        st.session_state.input_key += 1
        st.rerun()
    else:
        st.warning("Both fields must be filled.")

st.divider()

st.subheader("Existing Corrections")
if corrections:
    col_h1, col_h2, col_h3 = st.columns([2, 2, 1])
    col_h1.markdown("**Wrong**")
    col_h2.markdown("**Correct**")
    for wrong, correct in list(corrections.items()):
        c1, c2, c3 = st.columns([2, 2, 1])
        c1.write(wrong)
        c2.write(correct)
        if c3.button("DELETE", key=f"del_{wrong}"):
            delete_correction(wrong)
            st.session_state.correction_msg = f"Removed: '{wrong}'"
            st.rerun()
else:
    st.info("No corrections saved.")

if st.session_state.correction_msg:
    st.success(st.session_state.correction_msg)
    st.session_state.correction_msg = None