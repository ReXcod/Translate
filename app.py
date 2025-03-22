import streamlit as st
import speech_recognition as sr
from langdetect import detect
from googletrans import Translator
from elevenlabs import generate
import os
from io import BytesIO
import base64
import textwrap

# Supported languages
LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Marathi": "mr",
    "Latin": "la",
    "Greek": "el",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Chinese (Simplified)": "zh-cn",
    "Arabic": "ar",
    "Russian": "ru",
    "Portuguese": "pt"
}

# Voice mapping for ElevenLabs
VOICE_MAP = {
    "en": "Rachel",  # English
    "hi": "Priya",   # Hindi
    "mr": "Priya",   # Marathi (approximation)
    "la": "Adam",    # Latin
    "el": "Dimitri", # Greek
    "es": "Lucia",   # Spanish
    "fr": "Mimi",    # French
    "de": "Antoni",  # German
    "ja": "Rachel",  # Japanese (fallback)
    "zh-cn": "Rachel",  # Chinese (fallback)
    "ar": "Rachel",  # Arabic (fallback)
    "ru": "Rachel",  # Russian (fallback)
    "pt": "Lucia"    # Portuguese (approximation)
}

# Cached function to convert audio file to text
@st.cache_data
def audio_to_text(audio_file_content):
    recognizer = sr.Recognizer()
    with sr.AudioFile(BytesIO(audio_file_content)) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return "Could not understand the audio"
        except sr.RequestError:
            return "Could not request results; check your internet connection"

# Cached function to detect language
@st.cache_data
def detect_language(text):
    try:
        lang = detect(text)
        return lang
    except:
        return "unknown"

# Cached function to translate text (split into chunks for better accuracy)
@st.cache_data
def translate_text(text, dest_lang):
    translator = Translator()
    chunks = textwrap.wrap(text, 500)  # Split into smaller chunks
    translated_chunks = [translator.translate(chunk, dest=dest_lang).text for chunk in chunks]
    return " ".join(translated_chunks)

# Cached function to convert text to audio using ElevenLabs
@st.cache_data
def text_to_audio_elevenlabs(text, lang):
    try:
        voice = VOICE_MAP.get(lang, "Rachel")  # Default to Rachel if lang not found
        api_key = os.getenv("ELEVENLABS_API_KEY") or "sk_b92f5590f2870ebf5b9ee5f14d0f895007087eaad06a218e"  # Fallback to your key
        audio = generate(
            text=text,
            voice=voice,
            model="eleven_multilingual_v2",
            api_key=api_key
        )
        audio_file = BytesIO(audio)
        audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
        audio_html = f'<audio controls><source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3"></audio>'
        return audio_html
    except Exception as e:
        return f"Error generating audio with ElevenLabs: {str(e)}"

# Streamlit app
st.title("Language Translator with ElevenLabs TTS")
st.write("Upload a WAV file, choose input/output languages, and get natural-sounding translated audio!")

# Option to auto-detect or choose input language
input_mode = st.radio("Input Language Mode", ("Auto-Detect", "Manual Selection"))
input_lang_code = "auto"
if input_mode == "Manual Selection":
    input_lang_name = st.selectbox("Select Input Language", list(LANGUAGES.keys()))
    input_lang_code = LANGUAGES[input_lang_name]

# File uploader for audio input
upload_col, _ = st.columns(2)
with upload_col:
    uploaded_file = st.file_uploader("Choose an audio file (WAV)", type=["wav"])

# Language selection for output
output_lang_name = st.selectbox("Select Output Language", list(LANGUAGES.keys()))
output_lang_code = LANGUAGES[output_lang_name]

if uploaded_file is not None:
    # Read file content once
    audio_content = uploaded_file.read()

    # Convert audio to text
    with st.spinner("Processing audio..."):
        input_text = audio_to_text(audio_content)
    st.write("Recognized Text:", input_text)

    # Determine input language
    if input_text not in ["Could not understand the audio", "Could not request results; check your internet connection"]:
        if input_mode == "Auto-Detect":
            detected_lang = detect_language(input_text)
            st.write(f"Detected Input Language Code: {detected_lang}")
            if detected_lang == "unknown":
                st.error("Could not detect input language.")
                st.stop()
            input_lang_code = detected_lang
        else:
            st.write(f"Selected Input Language: {input_lang_name} ({input_lang_code})")

        # Translate to chosen language
        with st.spinner("Translating..."):
            translated_text = translate_text(input_text, output_lang_code)
        st.write(f"Translated Text ({output_lang_name}):", translated_text)

        # Convert translated text to audio with ElevenLabs
        with st.spinner("Generating audio..."):
            audio_output = text_to_audio_elevenlabs(translated_text, output_lang_code)
        st.write(f"{output_lang_name} Audio Output:")
        st.markdown(audio_output, unsafe_allow_html=True)
    else:
        st.error("Audio processing failed.")

st.write("Note: Uses ElevenLabs for natural audio. Your API key is included as a fallback; set ELEVENLABS_API_KEY in environment variables for security.")
