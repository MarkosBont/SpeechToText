import streamlit as st


def login_screen() -> None:
    st.markdown("""
    <style>
        .stButton > button {
            background-color: #2E7D32;
            color: white;
            border: none;
            padding: 0.6rem 0;
            font-weight: 500;
        }
        .stButton > button:hover {
            background-color: #1B5E20;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br>" * 3, unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Medical Transcription</h1>",
                unsafe_allow_html=True)

    left, mid, right = st.columns([1, 1.2, 1])
    with mid:
        st.button("Log in with Google", on_click=st.login, use_container_width=True)
