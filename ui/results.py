"""Displays the persisted result of the last recording (audio, text, download)."""

from datetime import datetime

import streamlit as st

import database
from ui.vocal_addition import render_vocal_addition


def render_results(user_id: str) -> None:
    if st.session_state.last_status is None:
        return

    st.divider()
    status = st.session_state.last_status
    polished = database.latest_polished(user_id)

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

        render_vocal_addition(user_id)

    elif status == "unknown":
        st.warning(polished)
    else:
        st.error(polished)
