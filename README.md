# AI-Multipurpose-Project

# 🌿 Readify AI

Welcome to **Readify AI**! This is a beginner-friendly, beautifully designed web application built with Python and Streamlit. Powered by Microsoft Azure AI, it helps you easily extract text from documents and convert text or images into lifelike speech.

## ✨ Features

The application is divided into three easy-to-use modules:

*   **📄 I. Document Intelligence (OCR):** Upload an image of a document (JPG/PNG) and instantly extract all the text from it. You can even download the result as a `.txt` file.
*   **🎙️ II. Speech Synthesis (TTS):** Type or paste any text, choose between a Male or Female voice, and generate a downloadable audio file (`.wav`).
*   **🔊 III. Image to Speech:** The ultimate combo! Upload an image containing text, and the app will automatically extract the text and read it out loud for you.

## 🛠️ Prerequisites

Before you start, you'll need:
1.  **Python** installed on your computer.
2.  An active **Microsoft Azure** account with resources created for:
    *   Computer Vision (for extracting text)
    *   Speech Services (for generating audio)

## 🚀 Quick Start Guide

### 1. Install Dependencies
Open your terminal or command prompt and run the following command to install the required Python libraries:

```bash
pip install streamlit pillow azure-cognitiveservices-vision-computervision msrest azure-cognitiveservices-speech
