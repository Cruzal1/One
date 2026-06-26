import streamlit as st
from streamlit_mic_recorder import speech_to_text
from deep_translator import GoogleTranslator

# Set page configuration
st.set_page_config(page_title="ESOL Live Translator", layout="wide", page_icon="🌐")

# Expanded Language Mapping
SPEECH = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Chinese (Simplified)": "zh-CN",
    "Arabic": "ar",
    "Hindi": "hi",
    "Vietnamese": "vi",
    "Japanese": "ja",
    "Portuguese": "pt",
    "Italian": "it",
    "Russian": "ru",
    "Korean": "ko",
    "Turkish": "tr",
    "Dutch": "nl"
    "Dari": "fa"
}
TRANS = SPEECH.copy()
langs = list(SPEECH.keys())

# Initialize session state
if "transcript" not in st.session_state:
    st.session_state.transcript = ""

@st.cache_data
def translate(text, s, t):
    if not text.strip():
        return ""
    if s == t:
        return text
    try:
        return GoogleTranslator(source=s, target=t).translate(text) or ""
    except Exception as e:
        return f"Translation Error: {e}"

# --- UI HEADER ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🌐 ESOL Live Translator App</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4B5563; font-size: 1.2rem;'>Speak into your microphone and get instant translations across multiple languages.</p>", unsafe_allow_html=True)
st.divider()

# Layout layout split
left, right = st.columns(2)

with left:
    st.markdown("### 🎛️ Input Controls")
    in_lang = st.selectbox("Select Input Language", langs)

    st.markdown("### 🎙️ Speak")
    mic = speech_to_text(
        start_prompt="🎙️ Start Listening",
        stop_prompt="🛑 Stop & Process",
        language=SPEECH[in_lang],
        key="mic"
    )

    # Animation / Processing indicator when audio is caught
    if mic:
        with st.spinner("✨ Transcribing and Translating..."):
            st.session_state.transcript = mic
            
    # Recognized text area (Editable fallback)
    edited = st.text_area(
        "Recognized Text (You can manually edit this if needed)",
        value=st.session_state.transcript,
        height=160
    )

    if edited != st.session_state.transcript:
        st.session_state.transcript = edited

    if st.button("🗑️ Clear Text", use_container_width=True):
        st.session_state.transcript = ""
        st.rerun()

with right:
    st.markdown("### 📢 Live Translations")
    
    # Defaults changed slightly to safely index within the expanded list
    for i, default in enumerate([1, 2, 3], start=1):
        out = st.selectbox(f"Output Language {i}", langs, index=default, key=f"o{i}")
        
        st.text_area(
            f"Translation {i}",
            value=translate(
                st.session_state.transcript,
                TRANS[in_lang],
                TRANS[out]
            ),
            height=100,
            disabled=True
        )
        if i < 3:
            st.divider()
