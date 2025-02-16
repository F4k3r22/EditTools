from moviepy import *
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.fx import Crop
from moviepy.video.fx import CrossFadeIn, CrossFadeOut, Loop
import os
from pathlib import Path
from .subt import Subt
import gc
import psutil

class VideoEditReddit:
    def __init__(self, video_background, tts_audio, font, title=None, text_size="medium", text_location="bottom", font_color="white", words=4,upper=False, lower=False, Final_screen=False, Text_final=None, music_audio=None, image_overlay=None, subtitles_path=None, overlay_duration=3, openai_api_key=None):
        """
        Initialize VideoEdit with necessary components
        
        Args:
            video_background (str): Path to background video
            tts_audio (str): Path to TTS audio file
            music_audio (str, optional): Path to background music
            image_overlay (str, optional): Path to image overlay
            subtitles_path (str, optional): Path to .srt subtitle file
            overlay_duration (int, optional): Duration in seconds for the overlay to appear (default: 3)
        """
        self.video_background = video_background
        self.tts_audio = tts_audio
        self.music_audio = music_audio
        self.image_overlay = image_overlay
        self.subtitles_path = str(Path(subtitles_path)) if subtitles_path else None
        self.output_size = (1080, 1920)  # Default to vertical video format
        self.overlay_duration = overlay_duration
        self.fade_duration = 0.5  # Duration of fade in/out effect in seconds
        self.openai_api_key = openai_api_key
        self.font = font
        self.font_color = font_color
        self.upper = upper
        self.lower = lower
        self.words = words
        self.font_size = text_size
        self.font_location = text_location
        self.title = title
        self.Final_screen = Final_screen
        self.Text_final = Text_final

    def text_size(self, text_size):
        """ Return the font size based on the text size """
        if text_size == "small":
            return 60
        elif text_size == "medium":
            return 90
        elif text_size == "large":
            return 120
        else:
            return 90
        
    def text_location(self, text_location):
        """ Return the text location based on the text location """
        if text_location == "top":
            return 'top'
        elif text_location == "bottom":
            return 'center'
        else:
            return 'center'
        
    def process_background(self, clip, duration):
        """
        Process background video to ensure correct dimensions and duration
        
        Args:
            clip: VideoFileClip to process
            duration: Target duration in seconds
        """
        # Check aspect ratio and crop if necessary
        if round((clip.w/clip.h), 4) < 0.5625:  # 9:16 aspect ratio
            crop_effect = Crop(
                width=clip.w,
                height=round(clip.w/0.5625),
                x_center=clip.w/2,
                y_center=clip.h/2
            )
            clip = crop_effect.apply(clip)
        else:
            crop_effect = Crop(
                width=round(0.5625*clip.h),
                height=clip.h,
                x_center=clip.w/2,
                y_center=clip.h/2
            )
            clip = crop_effect.apply(clip)
        
        # Resize to output dimensions
        clip = clip.resized(self.output_size)

        total_duration = duration + (5 if self.Final_screen else 0)
        
        # Loop or trim video to match audio duration
        if clip.duration < duration:
            loop_effect = Loop(duration=duration)
            final_clip = loop_effect.apply(clip)
            return final_clip
        else:
            clip = clip.with_duration(total_duration)
            
        return clip

    def create_overlay(self, duration):
        """Create overlay clip with transitions"""
        if not self.image_overlay:
            return None

        img = ImageClip(self.image_overlay)
        img = img.resized(width=self.output_size[0] * 0.8)
        img = img.with_position(("center", 500))
        img = img.with_duration(min(self.overlay_duration, duration))
    
        # Aplicar los efectos de crossfade
        #effects = [
        #    CrossFadeIn(duration=self.fade_duration),
        #    CrossFadeOut(duration=self.fade_duration)
        #]
        #img = img.with_effects(effects)
            
        return img


    def create_subtitle_clips(self, duration=None):
        print(f"Generando subtítulos desde: {self.subtitles_path}")
    
    # Verificar que existe el directorio fonts y el archivo de fuente
        #print(f"[DEBUG] Buscando fuente en: {font_path}")
    
        #if not os.path.exists(font_path):
        #    print(f"[ERROR] No se encontró el archivo de fuente en: {font_path}")
        #    return None

        #print(f"[DEBUG] Archivo de fuente encontrado, tamaño: {os.path.getsize(font_path)} bytes")
    
        try:

            def split_text(text):
                words = text.split()
    
                # Si no hay palabras, retornar texto vacío
                if not words:
                    return ''
        
                # Primero manejar el caso especial del punto
                if words[0] == '.':
                    if len(words) > 1:
                        processed_words = ['.'] + [words[1].capitalize()] + [w.lower() for w in words[2:]]
                    else:
                        processed_words = ['.']
                # Luego manejar las transformaciones de caso
                elif self.upper:
                    processed_words = [w.upper() for w in words]
                elif self.lower:
                    processed_words = [w.lower() for w in words]
                else:
                # Por defecto, primera palabra capitalizada, resto en minúsculas
                    processed_words = [words[0].capitalize()] + [w.lower() for w in words[1:]]
    
                # Unir palabras en grupos de 2 con salto de línea
                return '\n'.join(' '.join(processed_words[i:i+2]) for i in range(0, len(processed_words), 2))

            generator = lambda text: TextClip(font=self.font, text=split_text(text),
                                        font_size=self.text_size(self.font_size), color=(255,255,255,0) if text.strip() == '.' else self.font_color, text_align='center',      
                                        horizontal_align='center', 
                                        vertical_align=self.text_location(self.font_location),
                                        margin=(0, 700),
                                        interline=4, 
                                        stroke_color='black' if text.strip() != '.' else (0,0,0,0),  # Color del contorno
                                        stroke_width=10)   
                        
            subtitles = SubtitlesClip(
                    self.subtitles_path,
                    make_textclip=generator,
                    encoding='utf-8'  # Importante para caracteres especiales
                )
        
            if duration is not None:
                subtitles = subtitles.with_duration(duration)
        
            return subtitles
        
        except Exception as e:
            print(f"Error al crear clips de subtítulos: {str(e)}")
            import traceback
            print("Traceback completo:")
            print(traceback.format_exc())
            return None

    def generate_subtitles(self, output_path=None):
        """Generate subtitles with more robust path handling"""
        if not self.openai_api_key:
            raise ValueError("Se requiere OpenAI API key para generar subtítulos")
        
        try:
            # Determinar la ruta de salida
            if output_path is None:
                # Crear un directorio de subtítulos en el mismo directorio que el video
                base_dir = Path(self.video_background).parent
                subtitles_dir = base_dir / "subtitles"
                subtitles_dir.mkdir(parents=True, exist_ok=True)
                output_path = subtitles_dir / f"{Path(self.tts_audio).stem}.srt"
            else:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"Generando subtítulos en: {output_path}")
            
            # Generar subtítulos
            subt = Subt(api_key=self.openai_api_key, Final_screen=self.Final_screen, Text_final=self.Text_final)
            self.subtitles_path = subt.generate_subtitles_whisper(
                audio_path=self.tts_audio,
                words_per_subtitle=self.words,
                output_path=str(output_path)
            )

        # Si tenemos título, modificar el primer subtítulo
            if self.title:
                try:
                    with open(self.subtitles_path, 'r', encoding='utf-8') as f:
                        srt_lines = f.readlines()
                
                    modified_lines = []
                    i = 0
                    first_subtitle = True
                
                    while i < len(srt_lines):
                        if srt_lines[i].strip().isdigit():  # Número de subtítulo
                            modified_lines.append(srt_lines[i])  # Número
                            modified_lines.append(srt_lines[i + 1])  # Timestamp
                        
                            if first_subtitle:
                            # Para el primer subtítulo, reemplazar con un punto
                                modified_lines.append(".\n")
                                first_subtitle = False
                            else:
                                modified_lines.append(srt_lines[i + 2])  # Texto normal
                            
                            modified_lines.append(srt_lines[i + 3])  # Línea en blanco
                            i += 4
                        else:
                            i += 1

                # Escribir el archivo modificado
                    with open(self.subtitles_path, 'w', encoding='utf-8') as f:
                        f.writelines(modified_lines)
            
            # Verificar que el archivo se creó

                except Exception as e:
                    print(f"Error modificando subtítulos para el título: {str(e)}")
            
            if not os.path.exists(self.subtitles_path):
                raise FileNotFoundError(f"No se pudo generar el archivo de subtítulos en {self.subtitles_path}")
                
            return self.subtitles_path
            
        except Exception as e:
            print(f"Error al generar subtítulos: {str(e)}")
            raise

    def __del__(self):
        """Destructor de la clase para limpieza de memoria"""
        self.cleanup()

    def cleanup(self):
        """Método para limpiar recursos y liberar memoria"""
        try:
            # Limpieza de atributos grandes
            attributes_to_clean = [
                'video_background', 'tts_audio', 'music_audio', 
                'image_overlay', 'subtitles_path', 'font'
            ]
            
            for attr in attributes_to_clean:
                if hasattr(self, attr):
                    setattr(self, attr, None)

            # Forzar recolección de basura
            gc.collect()

            # Liberar memoria del sistema (opcional)
            if psutil.POSIX:  # Solo en sistemas POSIX (Linux/Unix)
                import resource
                resource.setrlimit(resource.RLIMIT_AS, (resource.RLIM_CUR, resource.RLIM_MAX))

        except Exception as e:
            print(f"Error durante la limpieza: {str(e)}")

    def mix_audio(self, tts_duration):
        """
            Mix TTS and background music if provided
    
            Args:
                tts_duration: Duration of the TTS audio in seconds
        """
        tts_audio = AudioFileClip(self.tts_audio)
        target_duration = tts_duration + (5 if self.Final_screen else 0)

        if self.music_audio:
            bg_music = AudioFileClip(self.music_audio)
        # Create a custom frame function that multiplies the original audio by 0.3
            original_frame_func = bg_music.frame_function
            bg_music.frame_function = lambda t: original_frame_func(t) * 0.1
        
        # Loop background music if shorter than target duration
            if bg_music.duration < target_duration:
                original_bg_func = bg_music.frame_function
                bg_music.frame_function = lambda t: original_bg_func(t % bg_music.duration)
                bg_music.duration = target_duration
                bg_music.end = target_duration
            else:
            # Trim background music if longer than target duration
                bg_music = bg_music.with_duration(target_duration)

        # Extend TTS audio with silence only for the portion after TTS ends
            if self.Final_screen:
                silence = AudioClip(lambda t: 0, duration=5)
                tts_extended = CompositeAudioClip([
                    tts_audio,
                    silence.with_start(tts_duration)
                ])
                final_audio = CompositeAudioClip([
                    tts_extended.with_duration(target_duration),
                    bg_music.with_duration(target_duration)
                ])
            else:
                final_audio = CompositeAudioClip([tts_audio, bg_music])
        else:
            if self.Final_screen:
                silence = AudioClip(lambda t: 0, duration=5)
                final_audio = CompositeAudioClip([
                    tts_audio,
                    silence.with_start(tts_duration)
                ])
            else:
                final_audio = tts_audio
    
        return final_audio

    def create_video(self, output_path="output.mp4", generate_subs=True):
        try:
            print("[DEBUG] Iniciando creación de video...")
            output_path = Path(output_path)
            output_dir = output_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)

            if generate_subs:
                print("[DEBUG] Intentando generar subtítulos...")
                srt_path = output_path.with_suffix('.srt')
                self.generate_subtitles(output_path=srt_path)
    
            print("[DEBUG] Procesando audio TTS...")
            tts_audio = AudioFileClip(self.tts_audio)
            tts_duration = tts_audio.duration
            total_duration = tts_duration + (5 if self.Final_screen else 0)
    
            print("[DEBUG] Procesando video de fondo...")
            video = VideoFileClip(self.video_background)
            video = self.process_background(video, tts_duration)  # process_background ya maneja la duración total
    
            video_components = [video]
    
            overlay = self.create_overlay(total_duration)
            if overlay:
                print("[DEBUG] Añadiendo overlay...")
                video_components.append(overlay)
    
            if self.subtitles_path and os.path.exists(self.subtitles_path):
                print("[DEBUG] Creando clips de subtítulos...")
                subtitles = self.create_subtitle_clips(duration=total_duration)
                if subtitles:
                    print("[DEBUG] Añadiendo subtítulos al video...")
                    subtitles = subtitles.with_position(('center', 'bottom'))
                    video_components.append(subtitles)
    
            print("[DEBUG] Componiendo video final...")
            final_video = CompositeVideoClip(video_components, size=self.output_size)
            final_video = final_video.with_duration(total_duration)
    
            print("[DEBUG] Mezclando audio...")
            final_audio = self.mix_audio(tts_duration)
            final_video = final_video.with_audio(final_audio)
    
            print(f"[DEBUG] Escribiendo video final en: {output_path}")
            final_video.write_videofile(
                str(output_path),
                fps=24,
                threads=64,
                codec='libx264',
                audio_codec='aac',
            )
    
        # Cleanup
            final_video.close()
            video.close()
            tts_audio.close()
            if self.music_audio:
                final_audio.close()

            self.cleanup_temp_files(output_path)
            self.cleanup()
        
        except Exception as e:
            print(f"Error creating video: {str(e)}")
            raise

    def cleanup_temp_files(self, output_path):
        """Limpia archivos temporales generados durante el proceso"""
        try:
            # Limpieza de archivos temporales de moviepy
            temp_files_patterns = [
                str(output_path).replace('.mp4', 'TEMP_MPY_wvf_snd.mp4'),
                '*.mpy',
                '*.mp4_temp',
                '*.mp4.temp'
            ]

            for pattern in temp_files_patterns:
                if '*' in pattern:
                    # Buscar archivos que coincidan con el patrón
                    import glob
                    for temp_file in glob.glob(pattern):
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                else:
                    # Eliminar archivo específico
                    if os.path.exists(pattern):
                        os.remove(pattern)

        except Exception as e:
            print(f"Error limpiando archivos temporales: {str(e)}")