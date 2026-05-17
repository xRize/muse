import json
from typing import List, Dict
from muse.models.track import Track
from muse.utils.paths import get_base_dir

class Playlist:
    def __init__(self, name: str, tracks: List[Track] = None):
        self.name = name
        self.tracks = tracks or []

    def to_dict(self):
        return {
            "name": self.name,
            "tracks": [t.to_dict() for t in self.tracks]
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            tracks=[Track.from_dict(t) for t in data.get("tracks", [])]
        )

class PlaylistManager:
    def __init__(self):
        self.playlists_file = get_base_dir() / "playlists.json"
        self.playlists: Dict[str, Playlist] = {}
        self.load()

    def load(self):
        if not self.playlists_file.exists():
            return
        try:
            with open(self.playlists_file, "r") as f:
                data = json.load(f)
                for name, pl_data in data.items():
                    self.playlists[name] = Playlist.from_dict(pl_data)
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to load playlists: {e}")

    def save(self):
        try:
            data = {name: pl.to_dict() for name, pl in self.playlists.items()}
            with open(self.playlists_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to save playlists: {e}")

    def create(self, name: str) -> bool:
        if name in self.playlists:
            return False
        self.playlists[name] = Playlist(name)
        self.save()
        return True

    def delete(self, name: str) -> bool:
        if name in self.playlists:
            del self.playlists[name]
            self.save()
            return True
        return False

    def get_playlist(self, name: str) -> Playlist:
        return self.playlists.get(name)

    def list_playlists(self) -> List[str]:
        return list(self.playlists.keys())
