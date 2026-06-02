import streamlit as st
import whisper
import tempfile
import os
import json
import time
from datetime import datetime
from filelock import FileLock
from audiorecorder import audiorecorder
from call import openai_call

# ── Corrections store ─────────────────────────────────────────────────────────
CORRECTIONS_FILE = "corrections.json"
CORRECTIONS_LOCK = "corrections.json.lock"

def load_corrections() -> dict:
    if not os.path.exists(CORRECTIONS_FILE):
        return {}
    with FileLock(CORRECTIONS_LOCK):
        with open(CORRECTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

def save_corrections(corrections: dict):
    with FileLock(CORRECTIONS_LOCK):
        with open(CORRECTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(corrections, f, ensure_ascii=False, indent=2)

# ── Whisper model ─────────────────────────────────────────────────────────────
@st.cache_resource()
def load_model():
    return whisper.load_model("medium")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Speech to Text", page_icon="🎙️", layout="centered")

if "last_transcript" not in st.session_state:
    st.session_state.last_transcript = ""
if "last_status" not in st.session_state:
    st.session_state.last_status = None
if "last_polished" not in st.session_state:
    st.session_state.last_polished = ""
if "prev_duration" not in st.session_state:
    st.session_state.prev_duration = 0
if "correction_msg" not in st.session_state:
    st.session_state.correction_msg = None

# ── Progress helper ───────────────────────────────────────────────────────────
def advance_progress(progress_bar, current: int, target: int, step_delay: float = 0.02):
    for val in range(current, target + 1):
        progress_bar.progress(val)
        time.sleep(step_delay)
    return target

# ── Core functions ────────────────────────────────────────────────────────────
def transcribe(audio_bytes: bytes, progress_bar, status_text):
    try:
        current = 0
        status_text.markdown("**⚙ Προετοιμασία αρχείου…**")
        current = advance_progress(progress_bar, current, 10)

        model = load_model()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        status_text.markdown("**Μεταγραφή ομιλίας...**")
        current = advance_progress(progress_bar, current, 30)

        result = model.transcribe(tmp_path, language="el", task="transcribe")
        os.unlink(tmp_path)
        text = result["text"].strip()

        status_text.markdown("**Μεταγραφή ολοκληρώθηκε.**")
        current = advance_progress(progress_bar, current, 60)

        return (text, "ok", current) if text else ("Δεν εντοπίστηκε ομιλία.", "unknown", current)
    except Exception as e:
        return f"Σφάλμα: {e}", "error", 0

def polish(transcript: str, progress_bar, status_text, current: int):
    status_text.markdown("**Polishing Text…**")
    current = advance_progress(progress_bar, current, 75)

    result = openai_call(transcript)

    status_text.markdown("**Απάντηση ελήφθη.**")
    current = advance_progress(progress_bar, current, 95)

    return result, current

# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='text-align: center;'>Medical Transcription</h1>", unsafe_allow_html=True)
st.divider()

# ── Recorder ──────────────────────────────────────────────────────────────────
btn_style = {
    "border": "1px solid #e2e8f0",
    "borderRadius": "6px",
    "padding": "12px 32px",
    "fontSize": "15px",
    "fontWeight": "600",
    "cursor": "pointer",
    "color": "#0f172a",
}

audio = audiorecorder(
    start_prompt="⏺  Start",
    pause_prompt="⏸  Pause",
    stop_prompt="⏹  Stop",
    start_style={**btn_style, "backgroundColor": "#10a103", "color": "#ffffff", "border": "1px solid #0f172a"},
    pause_style={**btn_style, "backgroundColor": "#e07604", "color": "#ffffff", "border": "1px solid #0f172a"},
    stop_style={**btn_style, "backgroundColor": "#c21104", "color": "#ffffff", "border": "1px solid #0f172a"},
    show_visualizer=True,
    key="recorder",
)

if len(audio) > 0:
    duration = audio.duration_seconds
    if duration != st.session_state.prev_duration:
        st.session_state.prev_duration = duration

        wav_buffer  = audio.export(format="wav")
        audio_bytes = wav_buffer.read()
        st.audio(audio_bytes, format="audio/wav")

        progress_bar = st.progress(0)
        status_text  = st.empty()

        transcript, status, current = transcribe(audio_bytes, progress_bar, status_text)
        st.session_state.last_transcript = transcript
        st.session_state.last_status     = status

        if status != "error":
            corrections = load_corrections()
            polished_transcript, current = polish(transcript, progress_bar, status_text, current)
            st.session_state.last_polished = polished_transcript
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
        st.code(polished, language=None, wrap_lines=True)
        st.download_button(
            "⬇ Download .txt",
            data=polished,
            file_name=f"transcript_{datetime.now().strftime('%H%M%S')}.txt",
            mime="text/plain",
        )
    elif status == "unknown":
        st.warning(polished)
    else:
        st.error(polished)

st.divider()
# ── Corrections manager ───────────────────────────────────────────────────────
corrections = load_corrections()


st.markdown("**Add a Correction:**")
col_a, col_b, col_c = st.columns([2, 2, 1])
wrong_word   = col_a.text_input("Wrong word",   key="new_wrong",   label_visibility="collapsed", placeholder="Wrong word")
correct_word = col_b.text_input("Correct word", key="new_correct", label_visibility="collapsed", placeholder="Correct word")
if col_c.button("Add"):
    if wrong_word.strip() and correct_word.strip():
        corrections[wrong_word.strip()] = correct_word.strip()
        save_corrections(corrections)
        st.session_state.correction_msg = f"Added: '{wrong_word}' → '{correct_word}'"
        st.rerun()
    else:
        st.warning("Both fields must be filled.")

st.markdown("**Existing Corrections**")
if corrections:
    col_h1, col_h2, col_h3 = st.columns([2, 2, 1])
    col_h1.markdown("**Wrong**")
    col_h2.markdown("**Correct**")
    col_h3.markdown("**Remove**")
    for wrong, correct in list(corrections.items()):
        c1, c2, c3 = st.columns([2, 2, 1])
        c1.write(wrong)
        c2.write(correct)
        if c3.button("🗑", key=f"del_{wrong}"):
            del corrections[wrong]
            save_corrections(corrections)
            st.session_state.correction_msg = f"Removed: '{wrong}'"
            st.rerun()
else:
    st.info("No corrections saved.")

if st.session_state.correction_msg:
    st.success(st.session_state.correction_msg)
    st.session_state.correction_msg = None