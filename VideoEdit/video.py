from moviepy import *
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.fx import Crop
from moviepy.video.fx import CrossFadeIn, CrossFadeOut
import os
from pathlib import Path

class VideoEdit:
    def __init__(self, video_background, tts_audio, music_audio=None, image_overlay=None, subtitles_path=None, overlay_duration=3):
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
        self.subtitles_path = subtitles_path
        self.output_size = (1080, 1920)  # Default to vertical video format
        self.overlay_duration = overlay_duration
        self.fade_duration = 0.5  # Duration of fade in/out effect in seconds
        
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
        img = img.with_position(('center', 'center'))
        img = img.with_duration(min(self.overlay_duration, duration))
    
        # Aplicar los efectos de crossfade
        effects = [
            CrossFadeIn(duration=self.fade_duration),
            CrossFadeOut(duration=self.fade_duration)
        ]
        img = img.with_effects(effects)
            
        return img

    def create_subtitle_clips(self, text_color="white", duration=None):
        """Create subtitle clips if subtitles are provided"""
        if not self.subtitles_path:
            return None
            
        generator = lambda txt: TextClip(
            txt,
            font="Arial",
            fontsize=100,
            color=text_color,
            stroke_color="black",
            stroke_width=5,
        )
        
        subtitles = SubtitlesClip(self.subtitles_path, generator)
        if duration is not None:
            subtitles = subtitles.with_duration(duration)
        return subtitles

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
            bg_music.frame_function = lambda t: original_frame_func(t) * 0.3
        
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

    def create_video(self, output_path="output.mp4"):
        """Create the final video with all components"""
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            output_path = str(Path(output_path))
            
            # Get TTS duration first as it determines final video length
            tts_audio = AudioFileClip(self.tts_audio)
            tts_duration = tts_audio.duration
            
            # Load and process background video
            video = VideoFileClip(self.video_background)
            video = self.process_background(video, tts_duration)
            
            # Create list of video components
            video_components = [video]
            
            # Add image overlay if provided
            overlay = self.create_overlay(tts_duration)
            if overlay:
                video_components.append(overlay)
            
            # Add subtitles if provided
            subtitles = self.create_subtitle_clips(duration=tts_duration)
            if subtitles:
                subtitles = subtitles.with_position(('center', 'bottom'))
                video_components.append(subtitles)
            
            # Compose video and set duration after creation
            final_video = CompositeVideoClip(video_components, size=self.output_size)
            final_video = final_video.with_duration(tts_duration)
            
            # Add audio
            final_audio = self.mix_audio(tts_duration)
            final_video = final_video.with_audio(final_audio)
            
            # Write final video
            final_video.write_videofile(
                output_path,
                fps=24,
                threads=32,
                codec='libx264',
                audio_codec='aac',
            )
            
            # Close all clips to free up resources
            final_video.close()
            video.close()
            tts_audio.close()
            if self.music_audio:
                final_audio.close()
                
        except Exception as e:
            print(f"Error creating video: {str(e)}")
            raise