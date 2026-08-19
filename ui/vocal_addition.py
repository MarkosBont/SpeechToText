"""Vocal addition section: record a follow-up note and merge it into the transcript."""

import streamlit as st
from audiorecorder import audiorecorder

import database
from audio_processing import transcribe_audio
from llm import openai_call_vocal_addition
from ui.widgets import advance_progress, center_recorders


def render_vocal_addition(user_id: str) -> None:
    st.subheader(":blue[Vocal Addition]")

    audio_addition = audiorecorder(
        "", "", "",
        show_visualizer=True,
        key=f"vocal_recorder_{st.session_state.vocal_recorder_key}",
    )
    center_recorders()

    if len(audio_addition) > 0:
        audio_bytes = audio_addition.export(format="mp3").read()

        progress_bar = st.progress(0)
        status_text = st.empty()

        current = 0
        status_text.markdown("**⚙ Προετοιμασία αρχείου…**")
        current = advance_progress(progress_bar, current, 10)

        status_text.markdown("**Μεταγραφή ομιλίας...**")
        current = advance_progress(progress_bar, current, 30)
        addition_transcript, add_status = transcribe_audio(audio_bytes)
        status_text.markdown("**Μεταγραφή ολοκληρώθηκε.**")
        current = advance_progress(progress_bar, current, 60)

        if add_status == "ok":
            status_text.markdown("**Polishing Text…**")
            current = advance_progress(progress_bar, current, 75)
            transcript_with_addition = openai_call_vocal_addition(
                user_id, st.session_state.base_polished, addition_transcript
            )
            status_text.markdown("**Απάντηση ελήφθη.**")
            current = advance_progress(progress_bar, current, 95)

            database.save_addition(user_id, addition_transcript, transcript_with_addition)

            advance_progress(progress_bar, current, 100)
            status_text.markdown("**Έτοιμο!**")
        elif add_status == "unknown":
            st.session_state.vocal_msg = ("warning", addition_transcript)
        else:
            st.session_state.vocal_msg = ("error", addition_transcript)

        st.session_state.vocal_recorder_key += 1
        st.rerun()

    if st.session_state.vocal_msg:
        kind, text = st.session_state.vocal_msg
        getattr(st, kind)(text)
        st.session_state.vocal_msg = None
