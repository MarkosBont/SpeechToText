import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_MED_API_KEY"))
supabase_client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_API_KEY"))


def configure_page() -> None:
    st.set_page_config(page_title="Speech to Text", page_icon="🎙️", layout="centered")
