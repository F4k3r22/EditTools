from openai import OpenAI
from testapi import API_KEY


def convert_whisper_to_srt(whisper_response):
    """
    Convierte la respuesta de Whisper a formato SRT con un estilo similar a AssemblyAI.
    """
    def format_timestamp(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def clean_text(text):
        # Normaliza la capitalización
        text = text.capitalize()
        # Corrige espacios múltiples
        text = ' '.join(text.split())
        return text

    srt_content = []
    subtitle_index = 1
    
    try:
        words = whisper_response.words
    except AttributeError:
        try:
            words = whisper_response.word
        except AttributeError:
            print("Estructura completa de la respuesta:")
            import json
            print(json.dumps(whisper_response.model_dump(), indent=2))
            raise Exception("No se pudo acceder a las palabras en la respuesta")

    current_subtitle = []
    current_start = None
    min_duration = 3.0  # Duración mínima similar a AssemblyAI (3 segundos)
    max_chars = 70  # Máximo de caracteres por línea
    
    for i, word in enumerate(words):
        if current_start is None:
            current_start = word.start
        
        try:
            word_text = word.word
        except AttributeError:
            try:
                word_text = word.value
            except AttributeError:
                print(f"Estructura de word: {word}")
                raise Exception("No se pudo acceder al texto de la palabra")
            
        current_subtitle.append(word_text)
        current_text = ' '.join(current_subtitle)
        
        # Condiciones para crear nuevo subtítulo
        should_split = False
        
        # 1. Por puntuación y longitud natural
        if any(punct in word_text for punct in '.!?'):
            should_split = True
        
        # 2. Por duración mínima y longitud máxima
        current_duration = word.end - current_start
        if (current_duration >= min_duration and len(current_text) >= max_chars):
            should_split = True
            
        # 3. Por final de palabras
        if i == len(words) - 1:
            should_split = True
        
        if should_split and current_subtitle:
            current_text = clean_text(current_text)
            
            # Asegurar duración mínima
            end_time = max(word.end, current_start + min_duration)
            
            srt_entry = f"{subtitle_index}\n"
            srt_entry += f"{format_timestamp(current_start)} --> {format_timestamp(end_time)}\n"
            srt_entry += f"{current_text}\n\n"
            
            srt_content.append(srt_entry)
            
            subtitle_index += 1
            current_subtitle = []
            current_start = None

    return ''.join(srt_content)

def generate_subtitles_whisper(audio_path):
    """
    Genera subtítulos usando la API de Whisper
    """
    client = OpenAI(api_key=API_KEY)
    
    with open(audio_path, "rb") as audio_file:
        print("Enviando solicitud a Whisper...")
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )
        
        print("Respuesta recibida de Whisper:")
        print(transcription)
        
        srt_content = convert_whisper_to_srt(transcription)
        
        # Guardar en archivo SRT
        srt_path = audio_path.replace('.mp3', '.srt')
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
            
        return srt_path

import assemblyai as aai
import os

def test_assemblyai_subtitles(audio_path: str, api_key: str) -> None:
    """
    Función de prueba para generar subtítulos con AssemblyAI
    """
    def __generate_subtitles_assemblyai(audio_path: str, voice: str) -> str:
        language_mapping = {
            "br": "pt",
            "id": "en",
            "jp": "ja",
            "kr": "ko",
        }
        
        if voice in language_mapping:
            lang_code = language_mapping[voice]
        else:
            lang_code = voice
            
        aai.settings.api_key = api_key
        config = aai.TranscriptionConfig(language_code=lang_code)
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(audio_path)
        subtitles = transcript.export_subtitles_srt()
        return subtitles

    # Probar diferentes idiomas
    test_voices = ["en", "es", "br", "jp"]
    
    for voice in test_voices:
        print(f"\nProbando con idioma: {voice}")
        try:
            subtitles = __generate_subtitles_assemblyai(audio_path, voice)
            print("Subtítulos generados:")
            print("-------------------")
            print(subtitles[:500])  # Mostrar los primeros 500 caracteres
            print("-------------------")
            
            # Guardar los subtítulos en un archivo
            output_file = f"subtitles_{voice}.srt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(subtitles)
            print(f"Subtítulos guardados en: {output_file}")
            
        except Exception as e:
            print(f"Error al generar subtítulos para {voice}: {str(e)}")


# Uso
if __name__ == "__main__":
    #API_KEY = "e87d9ef447c94868b581ac2a0cba7f8a"  # Reemplaza con tu API key
    #AUDIO_PATH = "/workspaces/codespaces-blank/EditTools/GenAPI/speech.mp3"  # Reemplaza con la ruta de tu archivo de audio
    
    #test_assemblyai_subtitles(AUDIO_PATH, API_KEY)

    print("-------------------")
    print("Probando con Whisper")
    print("-------------------")

    generate_subtitles_whisper("/workspaces/codespaces-blank/EditTools/GenAPI/speech.mp3")