import logging
import os
import tempfile
from pathlib import Path
from typing import List, Optional
import yt_dlp
import assemblyai as aai

from src.document_processing.doc_processor import DocumentChunk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YouTubeTranscriber:
    def __init__(self, assemblyai_api_key: str):
        self.assemblyai_api_key = assemblyai_api_key
        self.temp_dir = Path(tempfile.gettempdir()) / "youtube_transcriber"
        self.temp_dir.mkdir(exist_ok=True)
        
        aai.settings.api_key = assemblyai_api_key
        
        logger.info("YouTubeTranscriber initialized")
    
    def extract_video_id(self, url: str) -> Optional[str]:
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        else:
            video_id = None
        return video_id
    
    def download_audio(self, url: str) -> str:
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError("Could not extract video ID from URL")
        
        # Check for any existing audio file (not just m4a)
        existing_files = list(self.temp_dir.glob(f"{video_id}.*"))
        audio_extensions = ['.m4a', '.webm', '.mp3', '.opus', '.ogg', '.wav', '.mp4']
        for existing_file in existing_files:
            if existing_file.suffix.lower() in audio_extensions:
                logger.info(f"Audio already exists: {existing_file}")
                return str(existing_file)
        
        logger.info(f"Downloading audio from: {url}")
        
        # Try multiple strategies to avoid 403 errors and FFmpeg dependency
        # Strategy 1: Download audio-only format directly (no FFmpeg needed)
        strategies = [
            # Strategy 1: Best audio-only format, no postprocessing (Android client)
            {
                'format': 'bestaudio/bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio[ext=opus]/best[height<=480]/best',
                'outtmpl': str(self.temp_dir / '%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                },
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android'],
                    }
                },
                'retries': 3,
                'fragment_retries': 3,
            },
            # Strategy 2: Web client, audio-only
            {
                'format': 'bestaudio/bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio[ext=opus]/best[height<=480]/best',
                'outtmpl': str(self.temp_dir / '%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                },
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web'],
                    }
                },
                'retries': 3,
            },
            # Strategy 3: iOS client, any audio format
            {
                'format': 'bestaudio/best[height<=480]/best',
                'outtmpl': str(self.temp_dir / '%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios'],
                    }
                },
                'retries': 2,
            },
            # Strategy 4: Fallback - any available format, then try to extract audio if FFmpeg available
            {
                'format': 'best[height<=480]/best',
                'outtmpl': str(self.temp_dir / '%(id)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                }],
                'quiet': True,
                'no_warnings': True,
                'retries': 2,
            },
        ]
        
        last_error = None
        downloaded_file = None
        
        for i, ydl_opts in enumerate(strategies, 1):
            try:
                logger.info(f"Trying download strategy {i}/{len(strategies)}...")
                
                # Skip postprocessing strategies if FFmpeg is not available
                if 'postprocessors' in ydl_opts:
                    try:
                        import shutil
                        if not shutil.which('ffmpeg') and not shutil.which('ffprobe'):
                            logger.info(f"Skipping strategy {i} (requires FFmpeg, not available)")
                            continue
                    except:
                        logger.info(f"Skipping strategy {i} (requires FFmpeg, not available)")
                        continue
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    error_code = ydl.download([url])
                    
                    if error_code == 0:
                        # Find the downloaded file (could be various formats)
                        downloaded_files = list(self.temp_dir.glob(f"{video_id}.*"))
                        for file in downloaded_files:
                            if file.suffix.lower() in audio_extensions:
                                downloaded_file = file
                                break
                        
                        if downloaded_file and downloaded_file.exists():
                            logger.info(f"Audio downloaded successfully with strategy {i}: {downloaded_file}")
                            return str(downloaded_file)
                        else:
                            logger.warning(f"Strategy {i} completed but file not found")
                            continue
                    else:
                        logger.warning(f"Strategy {i} failed with error code: {error_code}")
                        continue
                        
            except Exception as e:
                last_error = e
                error_str = str(e)
                logger.warning(f"Strategy {i} failed: {error_str}")
                
                # Skip FFmpeg-related errors and try next strategy
                if "ffmpeg" in error_str.lower() or "ffprobe" in error_str.lower():
                    logger.info(f"Skipping strategy {i} due to FFmpeg requirement")
                    continue
                
                if "403" in error_str or "Forbidden" in error_str:
                    continue  # Try next strategy
                else:
                    # For other errors, continue to next strategy
                    continue
        
        # If all strategies failed
        error_msg = f"All download strategies failed. Last error: {str(last_error) if last_error else 'Unknown error'}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    def transcribe_youtube_video(
        self,
        url: str,
        cleanup_audio: bool = True
    ) -> List[DocumentChunk]:
        try:
            audio_path = self.download_audio(url)
            
            # Configure transcription with speaker diarization
            # AssemblyAI supports various audio formats, so we can use the downloaded file directly
            config = aai.TranscriptionConfig(
                speaker_labels=True,
                punctuate=True
            )
            
            logger.info(f"Starting transcription with speaker diarization for: {audio_path}")
            
            # Validate API key before attempting transcription
            if not self.assemblyai_api_key or self.assemblyai_api_key.strip() == "":
                raise ValueError("AssemblyAI API key is not set. Please set ASSEMBLYAI_API_KEY in your .env file.")
            
            try:
                transcriber = aai.Transcriber(config=config)
                transcript = transcriber.transcribe(audio_path)
            except Exception as upload_error:
                error_str = str(upload_error)
                if "401" in error_str or "Unauthorized" in error_str or "Invalid API key" in error_str:
                    raise ValueError(
                        "Invalid AssemblyAI API key. Please check your ASSEMBLYAI_API_KEY in the .env file. "
                        "Get a valid API key from https://www.assemblyai.com/"
                    ) from upload_error
                raise
            
            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"Transcription failed: {transcript.error}")
            
            chunks = []
            video_id = self.extract_video_id(url)
            for i, utterance in enumerate(transcript.utterances):
                chunk = DocumentChunk(
                    content=f"Speaker {utterance.speaker}: {utterance.text}",
                    source_file=f"YouTube Video {video_id}",
                    source_type="youtube",
                    page_number=None,
                    chunk_index=i,
                    start_char=utterance.start,
                    end_char=utterance.end,
                    metadata={
                        'speaker': utterance.speaker,
                        'start_time': utterance.start,
                        'end_time': utterance.end,
                        'confidence': getattr(utterance, 'confidence', None),
                        'video_url': url,
                        'video_id': video_id
                    }
                )
                chunks.append(chunk)
            
            logger.info(f"Transcription completed: {len(chunks)} utterances")
            
            if cleanup_audio and os.path.exists(audio_path):
                os.unlink(audio_path)
                logger.info("Audio file cleaned up")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error transcribing YouTube video: {str(e)}")
            raise
    
    def cleanup_temp_files(self):
        try:
            if self.temp_dir.exists():
                for file in self.temp_dir.glob("*.m4a"):
                    file.unlink()
                logger.info("Temporary files cleaned up")
        except Exception as e:
            logger.warning(f"Could not clean up temp files: {e}")


if __name__ == "__main__":
    import os
    
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not api_key:
        print("Please set ASSEMBLYAI_API_KEY environment variable")
        exit(1)
    
    transcriber = YouTubeTranscriber(api_key)
    
    try:
        test_url = "https://www.youtube.com/watch?v=D26sUZ6DHNQ"
        chunks = transcriber.transcribe_youtube_video(test_url)
        
        print(f"Transcribed {len(chunks)} utterances:")
        for chunk in chunks[:5]:
            print(f"  {chunk.content}")
        
    except Exception as e:
        print(f"Error: {e}")