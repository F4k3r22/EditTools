from openai import OpenAI
from pathlib import Path
import json

class Subt:
    def __init__(self, api_key, Final_screen=False, Text_final=None):
        """
        Inicializa el generador de subtítulos
        
        Args:
            api_key: OpenAI API key
            Final_screen: Si True, agrega un texto final
            Text_final: Texto a mostrar en la pantalla final
        """
        self.api_key = api_key
        self.Final_screen = Final_screen
        self.Text_final = Text_final
    
    def convert_whisper_to_srt(self, whisper_response, words_per_subtitle=4, min_duration=None):
        """
        Convierte la respuesta de Whisper a formato SRT con precisión de milisegundos
        
        Args:
            whisper_response: Respuesta de la API de Whisper
            words_per_subtitle: Número de palabras por subtítulo (default: 4)
            min_duration: Duración mínima en segundos (default: None para usar duración exacta)
            
        Returns:
            str: Contenido SRT formateado o string vacío en caso de error
        """
        def format_timestamp(seconds):
            try:
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                millis = round((seconds - int(seconds)) * 1000)
                return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
            except Exception as e:
                print(f"[ERROR] Error formateando timestamp {seconds}: {str(e)}")
                return "00:00:00,000"

        def clean_text(text):
            try:
                text = text.strip()
                text = text.capitalize()
                text = ' '.join(text.split())
                return text
            except Exception as e:
                print(f"[ERROR] Error limpiando texto: {str(e)}")
                return text

        def get_last_end_time(srt_content):
            try:
                if not srt_content:
                    return 0.0
                last_entry = srt_content[-1]
                time_str = last_entry.split('\n')[1].split(' --> ')[1].replace(',', '.')
                hours, minutes, seconds = time_str.split(':')
                total_seconds = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
                return total_seconds
            except Exception as e:
                print(f"[ERROR] Error obteniendo último tiempo: {str(e)}")
                return 0.0

        try:
            print("[DEBUG] Procesando respuesta de Whisper")
            
            # Convertir la respuesta a diccionario
            if hasattr(whisper_response, 'model_dump'):
                response_dict = whisper_response.model_dump()
            else:
                response_dict = whisper_response

            # Validar y extraer palabras
            words = response_dict.get('words', [])
            if not words:
                print("[WARNING] No se encontraron palabras en la respuesta")
                if self.Final_screen and self.Text_final:
                    return (
                        f"1\n"
                        f"{format_timestamp(0.5)} --> {format_timestamp(5.0)}\n"
                        f"{self.Text_final}\n\n"
                    )
                return ""

            print(f"[DEBUG] Encontradas {len(words)} palabras")

            # Inicializar variables
            srt_content = []
            subtitle_index = 1
            current_segment = []
            current_start = None
            current_end = None
            
            # Validar estructura de palabras
            for word in words:
                if 'start' not in word or 'end' not in word:
                    print(f"[WARNING] Palabra sin timestamps completos: {word}")
                    continue

                if current_start is None:
                    current_start = float(word.get('start', 0))
                    current_end = float(word.get('end', 0))

                word_text = word.get('word', '').strip()
                if not word_text:
                    continue

                current_segment.append(word_text)
                current_end = float(word.get('end', 0))

                # Determinar si crear nuevo segmento
                should_split = (
                    len(current_segment) >= words_per_subtitle or
                    any(punct in word_text for punct in '.!?,') or
                    word == words[-1]
                )

                if should_split and current_segment:
                    # Validar y ajustar tiempos
                    if current_end <= current_start:
                        current_end = current_start + 1.0

                    duration = current_end - current_start
                    if min_duration and duration < min_duration:
                        current_end = current_start + min_duration

                    subtitle_text = clean_text(' '.join(current_segment))

                    # Evitar superposición con subtítulo anterior
                    last_end = get_last_end_time(srt_content)
                    if current_start <= last_end:
                        current_start = last_end + 0.1
                        current_end = max(current_end, current_start + 0.5)

                    srt_entry = (
                        f"{subtitle_index}\n"
                        f"{format_timestamp(current_start)} --> {format_timestamp(current_end)}\n"
                        f"{subtitle_text}\n\n"
                    )
                    
                    srt_content.append(srt_entry)
                    subtitle_index += 1
                    current_segment = []
                    current_start = None
                    current_end = None

            # Agregar texto final si corresponde
            if self.Final_screen and self.Text_final and srt_content:
                try:
                    last_end = get_last_end_time(srt_content)
                    if last_end > 0:
                        final_start = last_end + 0.5
                        final_end = final_start + 4.5
                        
                        final_entry = (
                            f"{subtitle_index}\n"
                            f"{format_timestamp(final_start)} --> {format_timestamp(final_end)}\n"
                            f"{self.Text_final}\n\n"
                        )
                        
                        srt_content.append(final_entry)
                except Exception as e:
                    print(f"[WARNING] Error agregando texto final: {str(e)}")

            if not srt_content and self.Final_screen and self.Text_final:
                return (
                    f"1\n"
                    f"{format_timestamp(0.5)} --> {format_timestamp(5.0)}\n"
                    f"{self.Text_final}\n\n"
                )
            
            print(f"[DEBUG] Generados {len(srt_content)} subtítulos")

            print("[DEBUG] Lista de subtítulos generados:")
            for i, subtitle in enumerate(srt_content, 1):
                print(f"[DEBUG] Subtítulo #{i}:\n{subtitle}")

            return ''.join(srt_content)

        except Exception as e:
            print(f"[ERROR] Error al convertir respuesta Whisper a SRT: {str(e)}")
            print(f"[DEBUG] Estructura de la respuesta: {whisper_response}")
            if self.Final_screen and self.Text_final:
                return (
                    f"1\n"
                    f"{format_timestamp(0.5)} --> {format_timestamp(5.0)}\n"
                    f"{self.Text_final}\n\n"
                )
            return ""

    def generate_subtitles_whisper(self, audio_path, words_per_subtitle=4, min_duration=None, output_path=None):
        """
        Genera subtítulos usando la API de Whisper
        
        Args:
            audio_path: Ruta al archivo de audio
            words_per_subtitle: Número de palabras por subtítulo
            min_duration: Duración mínima en segundos
            output_path: Ruta de salida para el archivo SRT
            
        Returns:
            str: Ruta al archivo de subtítulos generado
            
        Raises:
            FileNotFoundError: Si no se encuentra el archivo de audio
            ValueError: Si no se puede generar el contenido SRT
        """
        try:
            print(f"[DEBUG] Iniciando generación de subtítulos para {audio_path}")
            client = OpenAI(api_key=self.api_key)
            
            # Validar archivo de entrada
            audio_path = Path(audio_path)
            if not audio_path.exists():
                raise FileNotFoundError(f"Archivo de audio no encontrado: {audio_path}")

            # Preparar ruta de salida
            if output_path is None:
                output_path = audio_path.with_suffix('.srt')
            else:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

            # Generar transcripción
            print(f"[DEBUG] Enviando solicitud a Whisper API...")
            with open(audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1",
                    response_format="verbose_json",
                    timestamp_granularities=["word"]
                )
            
            # Convertir a SRT
            print("[DEBUG] Convirtiendo transcripción a formato SRT")
            srt_content = self.convert_whisper_to_srt(
                transcription, 
                words_per_subtitle=words_per_subtitle,
                min_duration=min_duration
            )
            
            # Validar contenido SRT
            if not srt_content and not (self.Final_screen and self.Text_final):
                raise ValueError("No se generó contenido SRT")

            # Guardar archivo
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