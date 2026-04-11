# from gtts import gTTS
# import os
# import time

# def generate_audio(text, lang='hi'):
#     filename = f"translated_{int(time.time())}.mp3"
#     output_path = os.path.join("static", "outputs", "speech", filename)

#     tts = gTTS(text=text, lang=lang)
#     tts.save(output_path)

#     return filename