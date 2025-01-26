from moviepy import *
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.fx import Crop
from moviepy.video.fx import CrossFadeIn, CrossFadeOut
import os
from pathlib import Path
from .subt import Subt
import gc
import psutil

class VideoEditReddit:
    def __init__(self, video_background, tts_audio, font, font_color="white", words=4,upper=False, music_audio=None, image_overlay=None, subtitles_path=None, overlay_duration=3, openai_api_key=None):
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
        self.words = words
        
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
        
        # Loop or trim video to match audio duration
        if clip.duration < duration:
            clip = clip.loop(duration=duration)
        else:
            clip = clip.with_duration(duration)
            
        return clip

    def create_overlay(self, duration):
        """Create overlay clip with transitions"""
        if not self.image_overlay:
            return None

        img = ImageClip(self.image_overlay)
        img = img.resized(width=self.output_size[0] * 0.5)
        img = img.with_position(("center", 700))
        img = img.with_duration(min(self.overlay_duration, duration))
    
        # Aplicar los efectos de crossfade
        effects = [
            CrossFadeIn(duration=self.fade_duration),
            CrossFadeOut(duration=self.fade_duration)
        ]
        img = img.with_effects(effects)
            
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

            def split_text(text, upper=False):
                if upper:
                    text = text.upper()
                words = text.split()
                return '\n'.join(' '.join(words[i:i+2]) for i in range(0, len(words), 2))

            generator = lambda text: TextClip(font=self.font, text=split_text(text, upper=self.upper),
                                        font_size=90, color=self.font_color, text_align='center',      
                                        horizontal_align='center', 
                                        vertical_align='center',
                                        margin=(0, 700),
                                        interline=4, 
                                        stroke_color='black',  # Color del contorno
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
            subt = Subt(api_key=self.openai_api_key)
            self.subtitles_path = subt.generate_subtitles_whisper(
                audio_path=self.tts_audio,
                words_per_subtitle=self.words,
                output_path=str(output_path)
            )
            
            # Verificar que el archivo se creó
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
    
        if self.music_audio:
            bg_music = AudioFileClip(self.music_audio)
            # Create a custom frame function that multiplies the original audio by 0.3
            original_frame_func = bg_music.frame_function
            bg_music.frame_function = lambda t: original_frame_func(t) * 0.1
        
            # Loop background music if shorter than TTS
            if bg_music.duration < tts_duration:
                original_bg_func = bg_music.frame_function
                bg_music.frame_function = lambda t: original_bg_func(t % bg_music.duration)
                bg_music.duration = tts_duration
                bg_music.end = tts_duration
            else:
                # Trim background music if longer than TTS
                bg_music = bg_music.with_duration(tts_duration)
            
            final_audio = CompositeAudioClip([tts_audio, bg_music])
        else:
            final_audio = tts_audio
        
        return final_audio

    def create_video(self, output_path="output.mp4", generate_subs=True):
        """Create the final video with all components"""
        try:
            print("[DEBUG] Iniciando creación de video...")
            output_path = Path(output_path)
            output_dir = output_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)

            print(f"[DEBUG] Generando subtítulos: {generate_subs}")
            if generate_subs:
                print("[DEBUG] Intentando generar subtítulos...")
                srt_path = output_path.with_suffix('.srt')
                print(f"[DEBUG] Ruta de subtítulos: {srt_path}")
                self.generate_subtitles(output_path=srt_path)
        
            print("[DEBUG] Procesando audio TTS...")
            tts_audio = AudioFileClip(self.tts_audio)
            tts_duration = tts_audio.duration
        
            print("[DEBUG] Procesando video de fondo...")
            video = VideoFileClip(self.video_background)
            video = self.process_background(video, tts_duration)
        
            video_components = [video]
        
            overlay = self.create_overlay(tts_duration)
            if overlay:
                print("[DEBUG] Añadiendo overlay...")
                video_components.append(overlay)
        
            if self.subtitles_path and os.path.exists(self.subtitles_path):
                print(f"[DEBUG] Creando clips de subtítulos desde: {self.subtitles_path}")
                subtitles = self.create_subtitle_clips(duration=tts_duration)
                if subtitles:
                    print("[DEBUG] Añadiendo subtítulos al video...")
                    subtitles = subtitles.with_position(('center', 'bottom'))
                    video_components.append(subtitles)
        
            print("[DEBUG] Componiendo video final...")
            final_video = CompositeVideoClip(video_components, size=self.output_size)
            final_video = final_video.with_duration(tts_duration)
        
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

            temp_audio_file = str(output_path).replace('.mp4', 'TEMP_MPY_wvf_snd.mp4')
            if os.path.exists(temp_audio_file):
                try:
                    os.remove(temp_audio_file)
                    self.cleanup_temp_files(output_path)
                    self.cleanup()  # Llamar a la limpieza explícitamente
                    print(f"[DEBUG] Archivo temporal de audio eliminado: {temp_audio_file}")
                except Exception as e:
                    print(f"[WARNING] No se pudo eliminar el archivo temporal de audio: {str(e)}")
                
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