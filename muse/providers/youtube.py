import asyncio
import json
from ytmusicapi import YTMusic
from loguru import logger
from muse.models.track import Track

class YouTubeProvider:
    def __init__(self):
        self.ytm = YTMusic()

    async def search(self, query: str, limit: int = 5) -> list[Track]:
        logger.info(f"Searching YouTube Music for: {query}")
        # Run in executor since ytmusicapi is sync
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None, 
            lambda: self.ytm.search(query, filter="songs", limit=limit)
        )
        
        tracks = []
        for res in results:
            if res['resultType'] != 'song':
                continue
            
            artists = ", ".join([a['name'] for a in res.get('artists', [])])
            duration_str = res.get('duration', '0')
            duration = 0
            if ":" in duration_str:
                parts = duration_str.split(":")
                if len(parts) == 2:
                    duration = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

            tracks.append(Track(
                id=res['videoId'],
                title=res['title'],
                artist=artists,
                duration=duration,
                source="youtube",
                thumbnail=res.get('thumbnails', [{}])[0].get('url')
            ))
        
        return tracks

    async def resolve_stream_url(self, video_id: str) -> str:
        logger.info(f"Resolving stream URL for video: {video_id}")
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Use yt-dlp from the same environment if possible
        import sys
        import os
        yt_dlp_path = os.path.join(os.path.dirname(sys.executable), "yt-dlp")
        if not os.path.exists(yt_dlp_path):
            yt_dlp_path = "yt-dlp" # Fallback to PATH

        cmd = [
            yt_dlp_path,
            "-f", "bestaudio",
            "-g",
            url
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"yt-dlp error: {stderr.decode()}")
            raise RuntimeError(f"Failed to resolve stream URL: {stderr.decode()}")
        
        stream_url = stdout.decode().strip()
        return stream_url
