import streamlit as st

from config import configure_page
from ui.auth import login_screen
from ui.corrections import render_corrections_manager
from ui.recording import render_main_recorder
from ui.results import render_results

configure_page()

DEFAULT_SESSION_STATE = {
    "last_transcript": "",
    "last_status": None,
    "last_polished": "",
    "base_polished": "",
    "last_audio_bytes": None,
    "correction_msg": None,
    "input_key": 0,
    "main_recorder_key": 0,
    "vocal_recorder_key": 0,
    "vocal_msg": None,
}
for key, default in DEFAULT_SESSION_STATE.items():
    st.session_state.setdefault(key, default)

if not st.user.is_logged_in:
    login_screen()
    st.stop()

user_id = st.user["sub"]

st.markdown("<h1 style='text-align: center;'>Medical Transcription</h1>", unsafe_allow_html=True)
st.divider()

render_main_recorder(user_id)
render_results(user_id)
render_corrections_manager(user_id)

st.button("Logout", on_click=st.logout)
