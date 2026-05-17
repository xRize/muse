import os
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.easyid3 import EasyID3
from loguru import logger
from muse.models.track import Track

def extract_metadata(file_path: str) -> Track:
    """Extract metadata from an audio file."""
    title = os.path.basename(file_path)
    artist = "Unknown"
    duration = 0
    
    try:
        if file_path.lower().endswith('.mp3'):
            audio = MP3(file_path, ID3=EasyID3)
            title = audio.get('title', [title])[0]
            artist = audio.get('artist', ["Unknown"])[0]
            duration = int(audio.info.length)
        elif file_path.lower().endswith('.flac'):
            audio = FLAC(file_path)
            title = audio.get('title', [title])[0]
            artist = audio.get('artist', ["Unknown"])[0]
            duration = int(audio.info.length)
        elif file_path.lower().endswith('.ogg'):
            audio = OggVorbis(file_path)
            title = audio.get('title', [title])[0]
            artist = audio.get('artist', ["Unknown"])[0]
            duration = int(audio.info.length)
    except Exception as e:
        logger.debug(f"Metadata extraction failed for {file_path}: {e}")

    return Track(
        id=file_path,
        title=title,
        artist=artist,
        duration=duration,
        source="local",
        local_path=file_path
    )
