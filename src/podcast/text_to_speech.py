import logging
import os
import soundfile as sf
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass

try:
    from TTS.api import TTS
except ImportError:
    print("Coqui TTS not installed. Install with: pip install TTS>=0.22.0")
    TTS = None

from src.podcast.script_generator import PodcastScript

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AudioSegment:
    """Represents a single audio segment with metadata"""
    speaker: str
    text: str
    audio_data: Any
    duration: float
    file_path: str


class PodcastTTSGenerator:
    def __init__(self, model_name: str = "tts_models/en/ljspeech/tacotron2-DDC", sample_rate: int = 22050):
        if TTS is None:
            raise ImportError("Coqui TTS not available. Install with: pip install TTS>=0.22.0")
        
        self.sample_rate = sample_rate
        
        try:
            logger.info(f"Initializing Coqui TTS with model: {model_name}")
            # Initialize TTS with the specified model
            # Use GPU if available, otherwise CPU
            self.tts = TTS(model_name=model_name, progress_bar=True)
            logger.info("Coqui TTS initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Coqui TTS: {e}")
            raise ImportError(f"Failed to initialize Coqui TTS: {e}") from e
        
        # Map speakers to different voices/models
        # For multi-speaker, we can use different models or speaker IDs
        self.speaker_voices = {
            "Speaker 1": None,  # Default voice for Speaker 1
            "Speaker 2": None   # Default voice for Speaker 2
        }
        
        logger.info(f"Coqui TTS initialized with model='{model_name}', sample_rate={sample_rate}")
    
    def generate_podcast_audio(
        self, 
        podcast_script: PodcastScript,
        output_dir: str = "outputs/podcast_audio",
        combine_audio: bool = True
    ) -> List[str]:

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating podcast audio for {podcast_script.total_lines} segments")
        logger.info(f"Output directory: {output_dir}")
        
        audio_segments = []
        output_files = []
        
        for i, line_dict in enumerate(podcast_script.script):
            speaker, dialogue = next(iter(line_dict.items()))
            
            logger.info(f"Processing segment {i+1}/{podcast_script.total_lines}: {speaker}")
            
            try:
                segment_audio = self._generate_single_segment(speaker, dialogue)
                segment_filename = f"segment_{i+1:03d}_{speaker.replace(' ', '_').lower()}.wav"
                segment_path = os.path.join(output_dir, segment_filename)
                
                sf.write(segment_path, segment_audio, self.sample_rate)
                output_files.append(segment_path)
                
                if combine_audio:
                    audio_segment = AudioSegment(
                        speaker=speaker,
                        text=dialogue,
                        audio_data=segment_audio,
                        duration=len(segment_audio) / self.sample_rate,
                        file_path=segment_path
                    )
                    audio_segments.append(audio_segment)
                
                logger.info(f"✓ Generated segment {i+1}: {segment_filename}")
                
            except Exception as e:
                logger.error(f"✗ Failed to generate segment {i+1}: {str(e)}")
                continue
        
        if combine_audio and audio_segments:
            combined_path = self._combine_audio_segments(audio_segments, output_dir)
            output_files.append(combined_path)
        
        logger.info(f"Podcast generation complete! Generated {len(output_files)} files")
        return output_files
    
    def _generate_single_segment(self, speaker: str, text: str) -> Any:
        """Generate audio for a single text segment"""
        clean_text = self._clean_text_for_tts(text)
        
        try:
            # Generate audio using Coqui TTS
            # TTS.tts_to_file() writes to a file, so we'll use a temp file
            import tempfile
            import numpy as np
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                temp_path = tmp_file.name
            
            # Generate speech to file
            self.tts.tts_to_file(
                text=clean_text,
                file_path=temp_path
            )
            
            # Read the generated audio file
            audio_data, sample_rate = sf.read(temp_path)
            
            # Resample if needed
            if sample_rate != self.sample_rate:
                from scipy import signal
                num_samples = int(len(audio_data) * self.sample_rate / sample_rate)
                audio_data = signal.resample(audio_data, num_samples)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return audio_data.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            raise
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean and prepare text for TTS"""
        clean_text = text.strip()

        clean_text = clean_text.replace("...", ".")
        clean_text = clean_text.replace("!!", "!")
        clean_text = clean_text.replace("??", "?")

        if not clean_text.endswith(('.', '!', '?')):
            clean_text += '.'
        
        return clean_text
    
    def _combine_audio_segments(
        self, 
        segments: List[AudioSegment], 
        output_dir: str
    ) -> str:
        """Combine multiple audio segments into one file"""
        logger.info(f"Combining {len(segments)} audio segments")
        
        try:
            import numpy as np
            
            pause_duration = 0.3  # seconds
            pause_samples = int(pause_duration * self.sample_rate)
            pause_audio = np.zeros(pause_samples, dtype=np.float32)
            
            combined_audio = []
            for i, segment in enumerate(segments):
                combined_audio.append(segment.audio_data)
                
                if i < len(segments) - 1:
                    combined_audio.append(pause_audio)
            
            final_audio = np.concatenate(combined_audio)
            
            combined_filename = "complete_podcast.wav"
            combined_path = os.path.join(output_dir, combined_filename)
            sf.write(combined_path, final_audio, self.sample_rate)
            
            duration = len(final_audio) / self.sample_rate
            logger.info(f"✓ Combined podcast saved: {combined_path} (Duration: {duration:.1f}s)")
            
            return combined_path
            
        except Exception as e:
            logger.error(f"✗ Failed to combine audio segments: {str(e)}")
            raise


if __name__ == "__main__":
    try:
        tts_generator = PodcastTTSGenerator()
        
        sample_script_data = {
            "script": [
                {"Speaker 1": "Welcome everyone to our podcast! Today we're exploring the fascinating world of artificial intelligence."},
                {"Speaker 2": "Thanks for having me! AI is indeed one of the most exciting technological developments of our time."},
                {"Speaker 1": "Let's start with machine learning. Can you explain what makes it so revolutionary?"},
                {"Speaker 2": "Absolutely! Machine learning allows computers to learn from data without being explicitly programmed for every single task."},
            ]
        }
        
        from src.podcast.script_generator import PodcastScript
        test_script = PodcastScript(
            script=sample_script_data["script"],
            source_document="AI Overview Test",
            total_lines=len(sample_script_data["script"]),
            estimated_duration="2 minutes"
        )
        
        print("Generating podcast audio...")
        output_files = tts_generator.generate_podcast_audio(
            test_script,
            output_dir="./podcast_output",
            combine_audio=True
        )
        
        print(f"\nGenerated files:")
        for file_path in output_files:
            print(f"  - {file_path}")
        
        print("\nPodcast TTS test completed successfully!")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please install Coqui TTS: pip install TTS>=0.22.0")
    except Exception as e:
        print(f"Error: {e}")
