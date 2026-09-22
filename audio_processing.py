"""Audio cleanup and Whisper transcription."""

import os
import tempfile

from pydub import AudioSegment
from pydub.silence import detect_nonsilent

from config import openai_client as client


def strip_long_silences(
    seg: AudioSegment,
    min_silence_ms: int = 2000,   # only collapse pauses longer than this
    silence_thresh_db: int = -40,  # what counts as "silence" (dBFS)
    keep_ms: int = 300,           # padding kept around speech so words don't clip
) -> AudioSegment:
    spans = detect_nonsilent(seg, min_silence_len=min_silence_ms, silence_thresh=silence_thresh_db, seek_step=25)
    if not spans:
        return seg
    out = AudioSegment.empty()
    for start, end in spans:
        out += seg[max(0, start - keep_ms): min(len(seg), end + keep_ms)]
    return out


def transcribe_audio(audio_bytes: bytes) -> tuple[str, str]:
    """Send audio to Whisper. Returns (text, status), status one of
    'ok', 'unknown' (no speech detected) or 'error'."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="gpt-transcribe",
                file=audio_file,
                language="el",
            )
        text = result.text.strip()
        return (text, "ok") if text else ("Δεν εντοπίστηκε ομιλία.", "unknown")
    except Exception as e:
        return f"Σφάλμα: {e}", "error"
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
