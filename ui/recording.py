"""Main recording section: capture audio, transcribe, polish, persist."""

import streamlit as st
from audiorecorder import audiorecorder

import database
from audio_processing import strip_long_silences, transcribe_audio
from llm import openai_call
from ui.widgets import advance_progress, center_recorders


def render_main_recorder(user_id: str) -> None:
    st.subheader(":green[Main Recording]")
    audio = audiorecorder(
        "", "", "",
        show_visualizer=True,
        key=f"recorder_{st.session_state.main_recorder_key}",
    )
    center_recorders()

    if len(audio) == 0:
        return

    # stripped — this is what goes to Whisper AND what gets stored as last_audio_bytes
    stripped = strip_long_silences(audio)
    audio_bytes = stripped.export(format="mp3").read()
    st.session_state.last_audio_bytes = audio_bytes

    progress_bar = st.progress(0)
    status_text = st.empty()

    current = 0
    status_text.markdown("**⚙ Προετοιμασία αρχείου…**")
    current = advance_progress(progress_bar, current, 10)

    status_text.markdown("**Μεταγραφή ομιλίας...**")
    current = advance_progress(progress_bar, current, 30)
    transcript, status = transcribe_audio(audio_bytes)
    status_text.markdown("**Μεταγραφή ολοκληρώθηκε.**")
    current = advance_progress(progress_bar, current, 60)

    st.session_state.last_transcript = transcript
    st.session_state.last_status = status
    st.session_state.vocal_msg = None  # new transcription clears stale addition msg

    if status != "error":
        status_text.markdown("**Polishing Text…**")
        current = advance_progress(progress_bar, current, 75)
        polished_transcript = openai_call(user_id, transcript)
        status_text.markdown("**Απάντηση ελήφθη.**")
        current = advance_progress(progress_bar, current, 95)

        st.session_state.last_polished = polished_transcript
        st.session_state.base_polished = polished_transcript  # un-merged baseline for additions
        database.save_transcription(user_id, transcript, polished_transcript)

        status_text.markdown("**Saving to database...**")
        advance_progress(progress_bar, current, 100)
        status_text.markdown("**Έτοιμο!**")
    else:
        st.session_state.last_polished = transcript

    # consume this recording: refresh the main recorder so it can't reprocess,
    # and refresh the vocal recorder so the new transcription gets a clean,
    # empty addition recorder (mic shows, no stale state).
    st.session_state.main_recorder_key += 1
    st.rerun()
