from EditTools.GenAPI import TextGen, ClientTTS
from EditTools import SYSTEM_PROMPT_REDDIT
from text import Text_input_test
from EditTools.ImageEdit import EditImage
import json
from testapi import API_KEY
from EditTools.VideoEdit.video import VideoEditReddit
import os
from pathlib import Path

# Configurar la ruta base del proyecto
BASE_DIR = Path(__file__).parent

# Crear directorios necesarios
os.makedirs(BASE_DIR / "Videos", exist_ok=True)
os.makedirs(BASE_DIR / "output", exist_ok=True)

print("Test en estas clases y el generador de titulos")

# Test TextGen
Gen = TextGen(API_KEY, SYSTEM_PROMPT_REDDIT, Text_input_test)
response = Gen.generate()
print(response.choices[0].message.content)

print("Test del generador dinamico de imagenes")

content = json.loads(response.choices[0].message.content)

title = content["title"]
nickname = "chicodereddit"

# Generar imagen
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

# Definir rutas completas para los archivos
background_video = str(BASE_DIR / "videobackground.mp4")
music_audio = str(BASE_DIR / "musictiktok.mp3")
overlay_image = str(BASE_DIR / "imagen_editada.png")
tts_audio = str(output_path)  # El audio que generó ClientTTS

fontpath = str(BASE_DIR / "Arial_Bold.ttf")

if not os.path.exists(fontpath):
    raise FileNotFoundError(f"Archivo de fuente no encontrado en: {fontpath}")

# Crear directorio para subtítulos
subtitles_dir = BASE_DIR / "subtitles"
os.makedirs(subtitles_dir, exist_ok=True)
subtitles_path = str(subtitles_dir / "output.srt")

# Verificar que los archivos existan
if not os.path.exists(background_video):
    raise FileNotFoundError(f"Video de fondo no encontrado en: {background_video}")
if not os.path.exists(music_audio):
    print(f"Advertencia: Archivo de música no encontrado en: {music_audio}")
    music_audio = None
if not os.path.exists(overlay_image):
    print(f"Advertencia: Imagen de overlay no encontrada en: {overlay_image}")
    overlay_image = None
if not os.path.exists(tts_audio):
    raise FileNotFoundError(f"Audio TTS no encontrado en: {tts_audio}")

# Crear el editor de video
video_editor = VideoEditReddit(
    video_background=background_video,
    tts_audio=tts_audio,
    font=fontpath,
    music_audio=music_audio,
    image_overlay=overlay_image,
    subtitles_path=subtitles_path,
    overlay_duration=3,
    openai_api_key=API_KEY
)

# Generar el video final
output_video_path = str(BASE_DIR / "Videos" / "video8.mp4")
video_editor.create_video(output_video_path)

print(f"Video generado en {output_video_path}")