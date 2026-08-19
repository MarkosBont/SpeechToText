"""Small reusable Streamlit UI helpers."""

import time

import streamlit.components.v1 as components


def advance_progress(progress_bar, current: int, target: int, step_delay: float = 0.02) -> int:
    for val in range(current, target + 1):
        progress_bar.progress(val)
        time.sleep(step_delay)
    return target


def center_recorders() -> None:
    """Center the audiorecorder widget's iframe within the page."""
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
