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
if "prev_duration_main" not in st.session_state:
    st.session_state.prev_duration_main = 0
if "prev_duration_add" not in st.session_state:
    st.session_state.prev_duration_add = 0
if "correction_msg" not in st.session_state:
    st.session_state.correction_msg = None
if "input_key" not in st.session_state:
    st.session_state.input_key = 0

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

# ── Recorder ──────────────────────────────────────────────────────────────────
audio = audiorecorder("", "", "", show_visualizer=True, key="recorder")
center_recorders()

st.divider()

if len(audio) > 0:
    duration = audio.duration_seconds
    if duration != st.session_state.prev_duration_main:
        st.session_state.prev_duration_main = duration

        wav_buffer = audio.export(format="mp3")
        audio_bytes = wav_buffer.read()
        st.audio(audio_bytes, format="audio/mp3")

        progress_bar = st.progress(0)
        status_text  = st.empty()

        transcript, status, current = transcribe(audio_bytes, progress_bar, status_text)
        st.session_state.last_transcript = transcript
        st.session_state.last_status     = status

        if status != "error":
            polished_transcript, current = polish(transcript, progress_bar, status_text, current)
            st.session_state.last_polished = polished_transcript
            st.session_state.base_polished = polished_transcript   # un-merged baseline for additions
            advance_progress(progress_bar, current, 100)
            status_text.markdown("**Έτοιμο!**")
        else:
            st.session_state.last_polished = transcript

    else:
        wav_buffer = audio.export(format="wav")
        st.audio(wav_buffer.read(), format="audio/wav")

if st.session_state.last_status is not None:
    st.divider()
    status   = st.session_state.last_status
    polished = st.session_state.last_polished

    if status == "ok":
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

        audio_addition = audiorecorder("", "", "", show_visualizer=True, key="vocal_recorder")
        center_recorders()

        if len(audio_addition) > 0:
            duration = audio_addition.duration_seconds
            if duration != st.session_state.prev_duration_add:
                st.session_state.prev_duration_add = duration

                wav_buffer = audio_addition.export(format="mp3")
                audio_bytes = wav_buffer.read()
                st.audio(audio_bytes, format="audio/mp3")

                progress_bar = st.progress(0)
                status_text = st.empty()

                addition_transcript, status, current = transcribe(audio_bytes, progress_bar, status_text)
                st.session_state.last_transcript = addition_transcript
                st.session_state.last_status = status

                if status != "error":
                    transcript_with_addition, current = vocal_addition(
                        st.session_state.base_polished, addition_transcript,
                        progress_bar, status_text, current
                    )
                    st.session_state.last_polished = transcript_with_addition
                    advance_progress(progress_bar, current, 100)
                    status_text.markdown("**Έτοιμο!**")
                else:
                    st.session_state.last_polished = addition_transcript

            else:
                wav_buffer = audio_addition.export(format="wav")
                st.audio(wav_buffer.read(), format="audio/wav")

            if st.session_state.last_status is not None:
                st.divider()
                status = st.session_state.last_status

                if status == "ok":
                    st.markdown(st.session_state.last_polished)
                    st.download_button(
                        "⬇ Download .txt",
                        data=st.session_state.last_polished,
                        file_name=f"transcript_{datetime.now().strftime('%H%M%S')}.txt",
                        mime="text/plain",
                        key="download_addition",
                    )

                st.divider()

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