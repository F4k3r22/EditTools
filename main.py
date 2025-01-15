from GenAPI.GenAPI import TextGen, ClientTTS
from prompts import SYSTEM_PROMPT
from text import Text_input_test
from ImageEdit.edit import EditImage
import json
from testapi import API_KEY
from VideoEdit.video import VideoEdit

print("Test en estas clases y el generador de titulos")

# Test TextGen

Gen = TextGen(API_KEY, SYSTEM_PROMPT, Text_input_test)
response = Gen.generate()
print(response.choices[0].message.content)

print("Test del generador dinamico de imagenes")

content = json.loads(response.choices[0].message.content)

title = content["title"]
nickname = "chicodereddit"

EditImage(nickname, title)
print("Imagen generada")

text = content["text"]

voice_type = "alloy"

print("Test del generador de TTS")

GenTTS = ClientTTS(API_KEY, text, voice_type)

output_path = GenTTS.generateTTS()

print(f"Audio generado en {output_path}")


# Test VideoEdit
print("Test del editor de video")

background_video = "videobackground.mp4"
music_audio = "musictiktok.mp3"
overlay_image = f"imagen_editada.png"  # La imagen que generó EditImage
tts_audio = output_path  # El audio que generó ClientTTS

# Crear el editor de video
video_editor = VideoEdit(
    video_background=background_video,
    tts_audio=tts_audio,
    music_audio=music_audio,
    image_overlay=overlay_image,
    overlay_duration=3  # La imagen aparecerá los primeros 3 segundos
)

# Generar el video final
output_video_path = f"Videos/test.mp4"
video_editor.create_video(output_video_path)

print(f"Video generado en {output_video_path}")