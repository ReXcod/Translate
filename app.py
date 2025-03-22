import streamlit as st
import speech_recognition as sr
from langdetect import detect
from googletrans import Translator
from gtts import gTTS
import os
from io import BytesIO
import base64

# Supported languages for output (Google Translate and gTTS compatible)
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

# Function to convert audio file to text
def audio_to_text(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return "Could not understand the audio"
        except sr.RequestError:
            return "Could not request results; check your internet connection"

# Function to detect language
def detect_language(text):
    try:
        lang = detect(text)
        return lang
    except:
        return "unknown"

# Function to translate text to chosen language
def translate_text(text, dest_lang):
    translator = Translator()
    translated = translator.translate(text, dest=dest_lang)
    return translated.text

# Function to convert text to audio with gTTS
def text_to_audio(text, lang):
    try:
        # Adjust TLD for natural voice where applicable
        tld = 'co.in' if lang in ['hi', 'mr'] else 'com'  # Indian accent for Hindi/Marathi, default for others
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
st.title("Auto-Detect Language Translator with Custom Output")
st.write("Upload an audio file (WAV format), and choose your output language!")

# File uploader for audio input
uploaded_file = st.file_uploader("Choose an audio file", type=["wav"])

# Language selection for output
output_lang_name = st.selectbox("Select Output Language", list(LANGUAGES.keys()))
output_lang_code = LANGUAGES[output_lang_name]

if uploaded_file is not None:
    # Save uploaded file temporarily
    with open("temp_audio.wav", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Convert audio to text
    st.write("Processing audio...")
    input_text = audio_to_text("temp_audio.wav")
    st.write("Recognized Text:", input_text)

    # Detect input language
    detected_lang = detect_language(input_text)
    st.write(f"Detected Input Language Code: {detected_lang}")

    # Translate to chosen language
    if detected_lang != "unknown" and input_text != "Could not understand the audio":
        translated_text = translate_text(input_text, output_lang_code)
        st.write(f"Translated Text ({output_lang_name}):", translated_text)

        # Convert translated text to audio
        audio_output = text_to_audio(translated_text, output_lang_code)
        st.write(f"{output_lang_name} Audio Output:")
        st.markdown(audio_output, unsafe_allow_html=True)
    else:
        st.write("Unable to process audio or detect language.")

    # Clean up temporary file
    os.remove("temp_audio.wav")

st.write("Note: Upload a WAV file. Language detection uses 'langdetect'. Audio output uses gTTS with natural voice settings.")
