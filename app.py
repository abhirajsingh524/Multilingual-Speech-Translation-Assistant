from flask import Flask, render_template, request
import os

from models.translator import translate_text
# from models.text_to_speech import generate_audio

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads/audio"
OUTPUT_FOLDER = "static/outputs/speech"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/process', methods=['POST'])
def process():

    # audio = request.files['audio']
    # source_lang = request.form['source_lang']
    # target_lang = request.form['target_lang']

    # # Save file (optional for now)
    # audio_path = os.path.join(UPLOAD_FOLDER, audio.filename)
    # audio.save(audio_path)

    # 👉 TEMP: Instead of Whisper (for now)
    original_text = request.form.get("text", "Hello, how are you?")

    # Translate using MarianMT
    translated_text = translate_text(original_text)

    # # Generate audio
    # audio_file = generate_audio(translated_text)

    return render_template(
        "result.html",
        original_text=original_text,
        translated_text=translated_text,
    )


if __name__ == "__main__":
    app.run(debug=True)