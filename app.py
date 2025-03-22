import streamlit as st
import speech_recognition as sr
from langdetect import detect
from googletrans import Translator
from gtts import gTTS
import os
from io import BytesIO
import base64

# Supported languages (for both input and output)
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
    translated = translator.translate(text, dest=dest_lang)
    return translated.text

# Cached function to convert text to audio
@st.cache_data
def text_to_audio(text, lang):
    try:
        tld = 'co.in' if lang in ['hi', 'mr'] else 'com'
        tts = gTTS(text=text, lang=lang, slow=False, tld=tld)
        audio_file = BytesIO()
        tts.write_to_fp(audio_file)
        audio_file.seek(0)
        audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
        audio_html = f'<audio controls><source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3"></audio>'
        return audio_html
    except Exception as e:
        return f"Error generating audio: {str(e)}"

# Streamlit app
st.title("Optimized Language Translator")
st.write("Upload a WAV file, choose input/output languages, and get translated audio!")

# Option to auto-detect or choose input language
input_mode = st.radio("Input Language Mode", ("Auto-Detect", "Manual Selection"))
input_lang_code = "auto"
if input_mode == "Manual Selection":
    input_lang_name = st.selectbox("Select Input Language", list(LANGUAGES.keys()))
    input_lang_code = LANGUAGES[input_lang_name]

# File uploader for audio input
uploaded_file = st.file_uploader("Choose an audio file (WAV)", type=["wav"])

# Language selection for output
output_lang_name = st.selectbox("Select Output Language", list(LANGUAGES.keys()))
output_lang_code = LANGUAGES[output_lang_name]

if uploaded_file is not None:
    # Read file content once and reuse
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

        # Convert translated text to audio
        with st.spinner("Generating audio..."):
            audio_output = text_to_audio(translated_text, output_lang_code)
        st.write(f"{output_lang_name} Audio Output:")
        st.markdown(audio_output, unsafe_allow_html=True)
    else:
        st.error("Audio processing failed.")

st.write("Note: Upload WAV files only.")
