import os
from pathlib import Path
from loguru import logger
from muse.models.track import Track
from muse.models.config import Config
from muse.utils.fuzzy import fuzzy_match
from muse.utils.metadata import extract_metadata

class LocalProvider:
    def __init__(self, config: Config):
        self.config = config
        self.index: dict[str, Track] = {}
        self.paths = [os.path.expanduser(p) for p in config.library.paths]

    def scan(self):
        logger.info(f"Scanning library paths: {self.paths}")
        new_index = {}
        
        for base_path in self.paths:
            if not os.path.exists(base_path):
                logger.warning(f"Library path does not exist: {base_path}")
                continue
            
            for root, _, files in os.walk(base_path):
                for file in files:
                    if file.lower().endswith(('.mp3', '.flac', '.ogg')):
                        file_path = os.path.join(root, file)
                        try:
                            track = extract_metadata(file_path)
                            if track:
                                # Index by a combined string for better fuzzy matching
                                key = f"{track.title} {track.artist}".lower()
                                new_index[key] = track
                        except Exception as e:
                            logger.error(f"Error scanning {file_path}: {e}")
        
        self.index = new_index
        logger.info(f"Scanned {len(self.index)} local tracks")

    def search(self, query: str, threshold: int = 90) -> list[Track]:
        if not self.index:
            self.scan()
        
        if not self.index:
            return []

        results = fuzzy_match(query, list(self.index.keys()), threshold=threshold)
        
        tracks = []
        for match, score, _ in results:
            tracks.append(self.index[match])
        
        return tracks
