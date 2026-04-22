import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

LANGUAGE_MAP = {
    "en": "English",
    "hi": "Hindi",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "zh": "Chinese",
    "ar": "Arabic",
    "ru": "Russian",
    "it": "Italian",
    "pt": "Portuguese",
    "ja": "Japanese",
    "ko": "Korean",
    "bn": "Bengali",
    "ur": "Urdu",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
}

MODEL_NAME = "llama-3.3-70b-versatile"


def groq_translate(text, source_lang="en", target_lang="hi"):
    """Translate text using Groq's LLaMA model."""
    if not text.strip():
        return ""

    source = LANGUAGE_MAP.get(source_lang.lower(), "English")
    target = LANGUAGE_MAP.get(target_lang.lower(), "Hindi")

    prompt = f"""
Translate the following text from {source} to {target}.
Provide only the translated text without explanations.

Text:
{text}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are an expert multilingual translator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=1024,
    )

    return response.choices[0].message.content.strip()