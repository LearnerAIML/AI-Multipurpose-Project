import streamlit as st
import tempfile
import time
import os

# -----------------------------
# Azure Vision Imports
# -----------------------------
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials

# -----------------------------
# Azure Speech Imports
# -----------------------------
import azure.cognitiveservices.speech as speechsdk


# =========================================================
# AZURE CONFIG
# =========================================================

VISION_ENDPOINT = st.secrets["VISION_ENDPOINT"]
VISION_KEY = st.secrets["VISION_KEY"]

SPEECH_KEY = st.secrets["SPEECH_KEY"]
SPEECH_REGION = st.secrets["SPEECH_REGION"]


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Azure AI Multi Tool",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Azure AI Multi Tool")
st.markdown("Image → Text | Speech → Text | Text → Speech")


# =========================================================
# IMAGE TO TEXT
# =========================================================

st.header("🖼️ Image to Text (OCR)")

image_file = st.file_uploader(
    "Upload Image",
    type=["png", "jpg", "jpeg"],
    key="image_upload"
)

if image_file is not None:

    client = ComputerVisionClient(
        VISION_ENDPOINT,
        CognitiveServicesCredentials(VISION_KEY)
    )

    with tempfile.NamedTemporaryFile(delete=False) as temp_img:
        temp_img.write(image_file.read())
        image_path = temp_img.name

    with open(image_path, "rb") as image:
        read_response = client.read_in_stream(image, raw=True)

    operation_id = read_response.headers["Operation-Location"].split("/")[-1]

    with st.spinner("Extracting text from image..."):

        while True:
            result = client.get_read_result(operation_id)

            if result.status not in ["notStarted", "running"]:
                break

            time.sleep(1)

    extracted_text = ""

    if result.status == "succeeded":

        for page in result.analyze_result.read_results:
            for line in page.lines:
                extracted_text += line.text + "\n"

        st.success("Text Extracted Successfully")

        st.text_area(
            "Extracted Text",
            extracted_text,
            height=250
        )

    else:
        st.error("OCR Failed")

    os.remove(image_path)


st.divider()


# =========================================================
# SPEECH TO TEXT
# =========================================================

st.header("🎤 Speech to Text")

audio_file = st.file_uploader(
    "Upload Audio File",
    type=["wav"],
    key="audio_upload"
)

if audio_file is not None:

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_file.read())
        audio_path = temp_audio.name

    speech_config = speechsdk.SpeechConfig(
        subscription=SPEECH_KEY,
        region=SPEECH_REGION
    )

    speech_config.speech_recognition_language = "en-US"

    audio_config = speechsdk.audio.AudioConfig(filename=audio_path)

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )

    with st.spinner("Converting speech to text..."):
        result = recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:

        st.success("Speech Recognized")

        st.text_area(
            "Recognized Text",
            result.text,
            height=150
        )

    elif result.reason == speechsdk.ResultReason.NoMatch:
        st.error("No speech recognized")

    else:
        st.error("Speech recognition failed")

    os.remove(audio_path)


st.divider()


# =========================================================
# TEXT TO SPEECH
# =========================================================

st.header("🔊 Text to Speech")

input_text = st.text_area(
    "Enter text to convert into speech",
    height=150
)

if st.button("Generate Speech"):

    if input_text.strip() == "":
        st.warning("Please enter some text")

    else:

        speech_config = speechsdk.SpeechConfig(
            subscription=SPEECH_KEY,
            region=SPEECH_REGION
        )

        speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"

        output_file = "output_audio.wav"

        audio_config = speechsdk.audio.AudioConfig(
            filename=output_file
        )

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        with st.spinner("Generating speech..."):
            result = synthesizer.speak_text_async(input_text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:

            st.success("Speech generated successfully")

            with open(output_file, "rb") as audio:
                st.audio(audio.read(), format="audio/wav")

                st.download_button(
                    label="Download Audio",
                    data=audio,
                    file_name="generated_audio.wav",
                    mime="audio/wav"
                )

            os.remove(output_file)

        else:
            st.error("Text to Speech failed")