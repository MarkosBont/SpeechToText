"""Corrections manager: add/remove word-correction pairs for the current user."""

import streamlit as st

import database


def render_corrections_manager(user_id: str) -> None:
    corrections = database.load_corrections(user_id)

    st.divider()
    st.markdown("Add a Correction")
    col_a, col_b, col_c = st.columns([2, 2, 1])
    wrong_word = col_a.text_input(
        "Wrong word", key=f"new_wrong_{st.session_state.input_key}",
        label_visibility="collapsed", placeholder="Wrong word",
    )
    correct_word = col_b.text_input(
        "Correct word", key=f"new_correct_{st.session_state.input_key}",
        label_visibility="collapsed", placeholder="Correct word",
    )

    if col_c.button("Add"):
        if wrong_word.strip() and correct_word.strip():
            database.save_correction(user_id, wrong_word.strip(), correct_word.strip())
            st.session_state.correction_msg = f"Added: '{wrong_word}' → '{correct_word}'"
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.warning("Both fields must be filled.")

    with st.expander("Existing Corrections"):
        if corrections:
            col_h1, col_h2, col_h3 = st.columns([2, 2, 1])
            col_h1.markdown("**Wrong**")
            col_h2.markdown("**Correct**")
            for wrong, correct in list(corrections.items()):
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(wrong)
                c2.write(correct)
                if c3.button("DELETE", key=f"del_{wrong}"):
                    database.delete_correction(user_id, wrong)
                    st.session_state.correction_msg = f"Removed: '{wrong}'"
                    st.rerun()
        else:
            st.info("No corrections saved.")

    if st.session_state.correction_msg:
        st.success(st.session_state.correction_msg)
        st.session_state.correction_msg = None
