# -Multilingual-Speech-Translation-Assistant
Overview

The Multilingual Speech Translation Assistant is a Natural Language Processing (NLP) and Speech Processing project designed to enable seamless cross-language communication. The system captures spoken input, converts it into text using an Automatic Speech Recognition (ASR) model, and translates the transcribed text into a selected target language using a neural machine translation model.

This project demonstrates practical implementation of transformer architectures in real-world speech and language applications.

Key Features

Speech-to-Text transcription using state-of-the-art ASR

Multilingual translation using Transformer-based models

Support for multiple global languages

Audio file input support (.wav, .mp3)

Modular and scalable architecture

Optional text-to-speech output for translated text

Simple web interface (Streamlit / Flask)

Technologies Used

Python

PyTorch

OpenAI Whisper (ASR)

Transformer / Seq2Seq with Attention

Hugging Face Transformers

NumPy

Streamlit / Flask (Frontend Interface)

System Architecture

User provides speech input (microphone or audio file).

Audio is processed by the Whisper model for transcription.

Transcribed text is passed to a Transformer-based translation model.

Translated text is displayed to the user.

(Optional) Translated text is converted into speech output.

Models Used
1. Speech Recognition

Whisper (OpenAI)

Robust to noise and accents

Supports multilingual transcription

High transcription accuracy

2. Machine Translation

Transformer / Seq2Seq with Attention

Encoder–Decoder architecture

Self-attention mechanism

Context-aware translation

Pretrained multilingual translation models

