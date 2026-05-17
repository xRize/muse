import asyncio
import os
from loguru import logger
from muse.models.track import Track
from muse.utils.paths import get_download_dir
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

class DownloadManager:
    def __init__(self):
        self.download_dir = get_download_dir()

    async def download(self, track: Track) -> str:
        logger.info(f"Downloading track: {track.title} - {track.artist}")
        
        # Safe filename
        filename = f"{track.artist} - {track.title}.mp3".replace("/", "_")
        file_path = self.download_dir / filename
        
        if file_path.exists():
            logger.info(f"File already exists: {file_path}")
            return str(file_path)

        url = f"https://www.youtube.com/watch?v={track.id}"
        
        import sys
        yt_dlp_path = os.path.join(os.path.dirname(sys.executable), "yt-dlp")
        if not os.path.exists(yt_dlp_path):
            yt_dlp_path = "yt-dlp"

        cmd = [
            yt_dlp_path,
            "-f", "bestaudio",
            "--extract-audio",
            "--audio-format", "mp3",
            "-o", str(file_path),
            url
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Download failed: {stderr.decode()}")
            raise RuntimeError(f"Download failed: {stderr.decode()}")
        
        logger.info(f"Downloaded to {file_path}")
        
        # Tag metadata
        self._tag_metadata(file_path, track)
        
        return str(file_path)

    def _tag_metadata(self, file_path: str, track: Track):
        try:
            audio = MP3(file_path, ID3=EasyID3)
            audio['title'] = track.title
            audio['artist'] = track.artist
            audio.save()
            logger.info(f"Tagged metadata for {file_path}")
        except Exception as e:
            logger.error(f"Failed to tag metadata: {e}")
