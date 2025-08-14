from pathlib import Path
import pandas as pd
import streamlit as st

# Use Tkinter solely to pick a folder locally
import tkinter as tk
from tkinter import filedialog

st.set_page_config(page_title="Audio QA CSV Builder", layout="wide")
CSV_NAME = "audios.csv"     # per your request
AUDIO_EXT = ".wav"           # only .wav

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["filename", "file good or bad"])
if "folder" not in st.session_state:
    st.session_state.folder = ""

st.title("🎧 Audio QA CSV Builder")

with st.sidebar:
    st.header("Settings")
    st.caption("• Local folder only • Top-level files only • WAV only")
    st.caption("• Check the box if the audio is good (unchecked by default)")

def pick_folder_dialog() -> str:
    # Create a hidden Tk window, open a native directory chooser, then destroy
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    selected = filedialog.askdirectory(title="Select folder with .wav files")
    root.destroy()
    return selected or ""

def load_wavs_from_folder(folder: Path) -> pd.DataFrame:
    if not folder.exists() or not folder.is_dir():
        st.error("That path doesn't exist or isn't a folder.")
        return pd.DataFrame(columns=["filename", "file good or bad"])

    # Top-level only (no subfolders)
    files = [p for p in folder.glob("*") if p.is_file() and p.suffix.lower() == AUDIO_EXT]
    names = [p.name for p in files]
    df = pd.DataFrame({"filename": names, "file good or bad": False})
    return df

def save_csv_to_folder_text(csv_text: str, folder: Path, name: str = CSV_NAME) -> Path:
    out = folder / name
    out.write_text(csv_text, encoding="utf-8")
    return out

left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("1) Pick your folder")

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Browse…", type="primary", use_container_width=True):
            chosen = pick_folder_dialog()
            if chosen:
                st.session_state.folder = chosen

    with col2:
        st.text_input("Selected folder", value=st.session_state.folder, key="folder_display", disabled=True)

    if st.button("Load WAV files", use_container_width=True):
        if not st.session_state.folder:
            st.warning("Please choose a folder first.")
        else:
            base = Path(st.session_state.folder).expanduser().resolve()
            df = load_wavs_from_folder(base)
            st.session_state.df = df
            if not df.empty:
                st.success(f"Loaded {len(df)} .wav files from: {base}")
            else:
                st.warning("No .wav files found in that folder.")

with right:
    st.subheader("2) Review & label")
    if st.session_state.df.empty:
        st.info("Load a folder with .wav files to begin.")
    else:
        edited = st.data_editor(
            st.session_state.df,
            use_container_width=True,
            height=480,
            num_rows="fixed",
            column_config={
                "filename": st.column_config.TextColumn(disabled=True),
                "file good or bad": st.column_config.CheckboxColumn(
                    "file good or bad",
                    help="Check if the audio is good."
                )
            }
        )
        st.session_state.df = edited

        # Optional audio preview (local-playback)
        st.markdown("**Preview a file:**")
        choice = st.selectbox("Pick a file to play", ["(none)"] + edited["filename"].tolist(), index=0)
        if choice != "(none)" and st.session_state.folder:
            candidate = Path(st.session_state.folder) / choice
            if candidate.exists():
                try:
                    st.audio(candidate.read_bytes())
                except Exception as e:
                    st.warning(f"Could not play audio: {e}")

        # ---- CSV export with empty when unchecked ----
        df_out = edited.copy()
        col = "file good or bad"
        df_out[col] = df_out[col].map(lambda x: "TRUE" if x else "")

        csv_text = df_out.to_csv(index=False)
        csv_bytes = csv_text.encode("utf-8")

        # Download CSV
        st.download_button(
            "Download CSV",
            data=csv_bytes,
            file_name=CSV_NAME,
            mime="text/csv",
            use_container_width=True
        )

        # Also write to the same folder (one click)
        if st.session_state.folder:
            if st.button("Save CSV into selected folder", use_container_width=True):
                try:
                    out = save_csv_to_folder_text(csv_text, Path(st.session_state.folder), CSV_NAME)
                    st.success(f"Saved: {out}")
                except Exception as e:
                    st.error(f"Failed to save CSV: {e}")
