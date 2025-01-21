from openai import OpenAI
from pathlib import Path
import json

class Subt:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def convert_whisper_to_srt(self, whisper_response, words_per_subtitle=4):
        """Convierte la respuesta de Whisper a formato SRT con límite de 4 palabras por subtítulo"""
        def format_timestamp(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds - int(seconds)) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

        def clean_text(text):
            text = text.capitalize()
            text = ' '.join(text.split())
            return text

        try:
            print("[DEBUG] Procesando respuesta de Whisper")
            # Convertir la respuesta a diccionario si no lo es
            if hasattr(whisper_response, 'model_dump'):
                response_dict = whisper_response.model_dump()
            else:
                response_dict = whisper_response

            # Extraer las palabras
            words = response_dict.get('words', [])
            if not words:
                raise ValueError("No se encontraron palabras en la respuesta")

            print(f"[DEBUG] Encontradas {len(words)} palabras")

            # Inicializar variables para el procesamiento
            srt_content = []
            subtitle_index = 1
            current_segment = []
            current_start = None
            words_per_subtitle = words_per_subtitle  # Límite de palabras por subtítulo
            min_duration = 1.0  # Duración mínima en segundos
            
            print("[DEBUG] Iniciando procesamiento de palabras")
            
            for i, word in enumerate(words):
                # Obtener tiempo de inicio si es el inicio de un segmento
                if current_start is None:
                    current_start = float(word.get('start', 0))

                # Obtener el texto de la palabra
                word_text = word.get('word', '')
                if not word_text:
                    continue

                current_segment.append(word_text)

                # Determinar si debemos crear un nuevo segmento
                should_split = False
                
                # Split cuando alcanzamos 4 palabras
                if len(current_segment) >= words_per_subtitle:
                    should_split = True
                
                # Split en puntuación importante
                if any(punct in word_text for punct in '.!?'):
                    should_split = True
                
                # Split al final
                if i == len(words) - 1:
                    should_split = True

                if should_split and current_segment:
                    end_time = float(word.get('end', 0))
                    # Asegurar duración mínima
                    if end_time - current_start < min_duration:
                        end_time = current_start + min_duration

                    subtitle_text = clean_text(' '.join(current_segment))
                    
                    srt_entry = (
                        f"{subtitle_index}\n"
                        f"{format_timestamp(current_start)} --> {format_timestamp(end_time)}\n"
                        f"{subtitle_text}\n\n"
                    )
                    
                    srt_content.append(srt_entry)
                    subtitle_index += 1
                    current_segment = []
                    current_start = None

            print(f"[DEBUG] Generados {subtitle_index-1} subtítulos")
            return ''.join(srt_content)

        except Exception as e:
            print(f"[ERROR] Error al convertir respuesta Whisper a SRT: {str(e)}")
            print(f"[DEBUG] Estructura de la respuesta: {whisper_response}")
            raise

    def generate_subtitles_whisper(self, audio_path, words_per_subtitle=4, output_path=None):
        """Genera subtítulos usando la API de Whisper"""
        try:
            print(f"[DEBUG] Iniciando generación de subtítulos para {audio_path}")
            client = OpenAI(api_key=self.api_key)
            
            audio_path = Path(audio_path)
            if not audio_path.exists():
                raise FileNotFoundError(f"Archivo de audio no encontrado: {audio_path}")

            if output_path is None:
                output_path = audio_path.with_suffix('.srt')
            else:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"[DEBUG] Enviando solicitud a Whisper API...")
            with open(audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1",
                    response_format="verbose_json",
                    timestamp_granularities=["word"]
                )
            
            print("[DEBUG] Convirtiendo transcripción a formato SRT")
            srt_content = self.convert_whisper_to_srt(transcription, words_per_subtitle=words_per_subtitle)
            
            if not srt_content:
                raise ValueError("No se generó contenido SRT")

            print(f"[DEBUG] Guardando subtítulos en {output_path}")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)

            if not output_path.exists():
                raise FileNotFoundError(f"No se pudo crear el archivo de subtítulos en {output_path}")

            print(f"[DEBUG] Subtítulos generados exitosamente")
            return str(output_path)

        except Exception as e:
            print(f"[ERROR] Error en generate_subtitles_whisper: {str(e)}")
            raise