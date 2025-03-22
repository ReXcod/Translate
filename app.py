import streamlit as st
import speech_recognition as sr
from langdetect import detect
from googletrans import Translator
from elevenlabs import generate
import os
import requests
from io import BytesIO
import base64
import textwrap
import random

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

# Function to get all available voices from ElevenLabs
@st.cache_data
def get_available_voices(api_key):
    try:
        response = requests.get("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": api_key})
        voices = response.json().get("voices", [])
        if voices:
            return [voice["voice_id"] for voice in voices]  # Return list of voice IDs
        return ["Rachel"]  # Fallback to Rachel if no voices found
    except Exception:
        return ["Rachel"]  # Fallback in case of error

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

# Cached function to translate text
@st.cache_data
def translate_text(text, dest_lang):
    translator = Translator()
    chunks = textwrap.wrap(text, 500)
    translated_chunks = [translator.translate(chunk, dest=dest_lang).text for chunk in chunks]
    return " ".join(translated_chunks)

# Function to convert text to audio with a random voice (not cached due to randomness)
def text_to_audio_elevenlabs(text, lang, voices):
    try:
        voice = random.choice(voices)  # Pick a random voice each time
        api_key = os.getenv("ELEVENLABS_API_KEY") or "sk_b92f5590f2870ebf5b9ee5f14d0f895007087eaad06a218e"
        audio = generate(
            text=text,
            voice=voice,
            model="eleven_multilingual_v2",
            api_key=api_key
        )
        audio_file = BytesIO(audio)
        audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
        audio_html = f'<audio controls><source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3"></audio>'
        return audio_html, voice  # Return audio HTML and the voice used
    except Exception as e:
        return f"Error generating audio with ElevenLabs: {str(e)}", None

# Streamlit app
st.title("Language Translator with Random ElevenLabs Voices")
st.write("Upload a WAV file, choose input/output languages, and get translated audio with a random voice!")

# Get available voices at startup
api_key = os.getenv("ELEVENLABS_API_KEY") or "sk_b92f5590f2870ebf5b9ee5f14d0f895007087eaad06a218e"
available_voices = get_available_voices(api_key)
st.write(f"Available Voices: {', '.join(available_voices)}")

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
    audio_content = uploaded_file.read()
    with st.spinner("Processing audio..."):
        input_text = audio_to_text(audio_content)
    st.write("Recognized Text:", input_text)

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

        with st.spinner("Translating..."):
            translated_text = translate_text(input_text, output_lang_code)
        st.write(f"Translated Text ({output_lang_name}):", translated_text)

        with st.spinner("Generating audio..."):
            audio_output, used_voice = text_to_audio_elevenlabs(translated_text, output_lang_code, available_voices)
        st.write(f"{output_lang_name} Audio Output (Voice: {used_voice}):")
        st.markdown(audio_output, unsafe_allow_html=True)
    else:
        st.error("Audio processing failed.")

st.write("Note: Uses a random ElevenLabs voice each time. Set ELEVENLABS_API_KEY in environment variables for security.")
